# coding: utf-8

from django.views import generic
from django.utils.decorators import method_decorator
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from member.models import (
    Client,
    Member,
    Address,
    Contact,
    Referencing,
    Restriction,
    Client_option,
    ClientFilter,
    ClientFilter,
    DAYS_OF_WEEK,
    Route,
    Client_avoid_ingredient,
    Client_avoid_component,
)
from note.models import Note
from order.models import Order
from meal.models import Restricted_item
from meal.models import COMPONENT_GROUP_CHOICES
from formtools.wizard.views import NamedUrlSessionWizardView
from django.core.urlresolvers import reverse_lazy
import csv
from django.template import RequestContext
from django.http import JsonResponse

size = ['regular', 'large']

meals = ['main_dish', 'dessert', 'diabetic', 'fruit_salad',
         'green_salad', 'pudding', 'compote']

day_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
               'saturday', 'sunday']

meals_template = ['main_dish', 'dessert', 'diabetic', 'fruit_salad',
                  'green_salad'
                  ]


class ClientWizard(NamedUrlSessionWizardView):

    template_name = 'forms/form.html'

    def get_context_data(self, **kwargs):
        context = super(ClientWizard, self).get_context_data(**kwargs)

        context["weekday"] = DAYS_OF_WEEK
        context["meals"] = COMPONENT_GROUP_CHOICES

        return context

    def save_json(self, dictonary):
        json = {}

        for days, Days in DAYS_OF_WEEK:
            json['size_{}'.format(days)] = dictonary.cleaned_data.get(
                'size_{}'.format(days)
            )

            if json['size_{}'.format(days)] is "":
                json['size_{}'.format(days)] = None

            for meal, Meals in COMPONENT_GROUP_CHOICES:
                json['{}_{}_quantity'.format(meal, days)] \
                    = dictonary.cleaned_data.get(
                    '{}_{}_quantity'.format(meal, days)
                )

        return json

    def done(self, form_list, form_dict, **kwargs):

        self.form_dict = form_dict
        self.save()
        return HttpResponseRedirect(reverse_lazy('member:list'))

    def save(self):
        """Save the client"""

        address = self.save_address()
        member = self.save_member(address)
        billing_member = self.save_billing_member(member)
        emergency = self.save_emergency_contact(billing_member)
        client = self.save_client(member, billing_member, emergency)
        self.save_referent_information(client, billing_member, emergency)
        self.save_preferences(client)

    def save_address(self):
        address_information = self.form_dict['address_information']

        address = Address.objects.create(
            number=address_information.cleaned_data.get('number'),
            street=address_information.cleaned_data.get('street'),
            apartment=address_information.cleaned_data.get(
                'apartment'
            ),
            floor=address_information.cleaned_data.get('floor'),
            city=address_information.cleaned_data.get('city'),
            postal_code=address_information.cleaned_data.get('postal_code'),
            latitude=address_information.cleaned_data.get('latitude'),
            longitude=address_information.cleaned_data.get('longitude'),
            distance=address_information.cleaned_data.get('distance'),
        )

        address.save()
        return address

    def save_member(self, address):
        basic_information = self.form_dict['basic_information']

        member = Member.objects.create(
            firstname=basic_information.cleaned_data.get('firstname'),
            lastname=basic_information.cleaned_data.get('lastname'),
            address=address,
        )
        member.save()

        contact = Contact.objects.create(
            type=basic_information.cleaned_data.get('contact_type'),
            value=basic_information.cleaned_data.get("contact_value"),
            member=member,
        )
        contact.save()

        return member

    def save_billing_member(self, member):
        payment_information = \
            self.form_dict['payment_information'].cleaned_data

        if payment_information.get('same_as_client'):
            billing_member = member

        else:
            e_b_member = payment_information.get('member')
            if self.billing_member_is_member():
                billing_member = member
            elif e_b_member:
                e_b_member_id = e_b_member.split(' ')[0].\
                    replace('[', '').replace(']', '')
                billing_member = Member.objects.get(pk=e_b_member_id)
            else:
                billing_address = Address.objects.create(
                    number=payment_information.get('number'),
                    street=payment_information.get('street'),
                    apartment=payment_information.get('apartment'),
                    floor=payment_information.get('floor'),
                    city=payment_information.get('city'),
                    postal_code=payment_information.get('postal_code'),
                )
                billing_address.save()

                billing_member = Member.objects.create(
                    firstname=payment_information.get('firstname'),
                    lastname=payment_information.get('lastname'),
                    address=billing_address,
                )
                billing_member.save()

        return billing_member

    def save_emergency_contact(self, billing_member):
        emergency_contact = self.form_dict['emergency_contact']
        e_emergency_member = emergency_contact.cleaned_data.get('member')
        if self.billing_member_is_emergency_contact(billing_member):
            emergency = billing_member
        elif e_emergency_member:
            e_emergency_member_id = e_emergency_member.split(' ')[0]\
                .replace('[', '')\
                .replace(']', '')
            emergency = Member.objects.get(pk=e_emergency_member_id)
        else:
            emergency = Member.objects.create(
                firstname=emergency_contact.cleaned_data.get("firstname"),
                lastname=emergency_contact.cleaned_data.get('lastname'),
            )
            emergency.save()

        client_emergency_contact = Contact.objects.create(
            type=emergency_contact.cleaned_data.get("contact_type"),
            value=emergency_contact.cleaned_data.get(
                "contact_value"
            ),

            member=emergency,
        )
        client_emergency_contact.save()
        return emergency

    def save_client(self, member, billing_member, emergency):
        dietary_restriction = self.form_dict['dietary_restriction']
        payment_information = self.form_dict['payment_information']
        basic_information = self.form_dict['basic_information']
        address_information = self.form_dict['address_information']
        # Client SAVE
        client = Client.objects.create(
            rate_type=payment_information.cleaned_data.get("facturation"),
            billing_payment_type=payment_information.cleaned_data.get(
                "billing_payment_type"),
            member=member,
            billing_member=billing_member,
            emergency_contact=emergency,
            language=basic_information.cleaned_data.get('language'),
            gender=basic_information.cleaned_data.get('gender'),
            birthdate=basic_information.cleaned_data.get('birthdate'),
            alert=basic_information.cleaned_data.get("alert"),
            delivery_type=dietary_restriction.cleaned_data.get(
                "delivery_type"
            ), meal_default_week=self.save_json(dietary_restriction),
            route=Route.objects.get(
                name=address_information.cleaned_data.get('route')),
            delivery_note=address_information.cleaned_data.get('delivery_note')
        )
        if dietary_restriction.cleaned_data.get('status'):
            client.status = 'A'

        client.save()
        return client

    def save_referent_information(self, client, billing_member, emergency):
        referent_information = self.form_dict['referent_information']
        e_referent = referent_information.cleaned_data.get('member')
        if self.referent_is_billing_member():
            referent = billing_member
        elif self.referent_is_emergency_contact():
            referent = emergency
        elif e_referent:
            e_referent_id = e_referent.split(' ')[0]\
                .replace('[', '')\
                .replace(']', '')
            referent = Member.objects.get(pk=e_referent_id)
        else:
            referent = Member.objects.create(
                firstname=referent_information.cleaned_data.get("firstname"),
                lastname=referent_information.cleaned_data.get("lastname"),
            )
            referent.save()

        referencing = Referencing.objects.create(
            referent=referent,
            client=client,
            referral_reason=referent_information.cleaned_data.get(
                "referral_reason"
            ),
            work_information=referent_information.cleaned_data.get(
                'work_information'
            ),
            date=referent_information.cleaned_data.get(
                'date'
            ),
        )
        referencing.save()
        return referencing

    def save_preferences(self, client):
        preferences = self.form_dict['dietary_restriction'].cleaned_data

        # Save restricted items
        for restricted_item in preferences.get('restrictions'):
            Restriction.objects.create(
                client=client,
                restricted_item=restricted_item
            )

        # Save food preparation
        for food_preparation in preferences.get('food_preparation'):
            Client_option.objects.create(
                client=client,
                option=food_preparation
            )

        # Save ingredients to avoid
        for ingredient_to_avoid in preferences.get('ingredient_to_avoid'):
            Client_avoid_ingredient.objects.create(
                client=client,
                ingredient=ingredient_to_avoid
            )

        # Save components to avoid
        for component_to_avoid in preferences.get('dish_to_avoid'):
            Client_avoid_component.objects.create(
                client=client,
                component=component_to_avoid
            )

    def billing_member_is_member(self):
        basic_information = self.form_dict['basic_information']
        payment_information = self.form_dict['payment_information']

        b_firstname = basic_information.cleaned_data.get('firstname')
        b_lastname = basic_information.cleaned_data.get('lastname')

        p_firstname = payment_information.cleaned_data.get('firstname')
        p_lastname = payment_information.cleaned_data.get('lastname')

        if b_firstname == p_firstname and b_lastname == p_lastname:
            return True
        return False

    def billing_member_is_emergency_contact(self, billing_member):
        emergency_contact = self.form_dict['emergency_contact']

        e_firstname = emergency_contact.cleaned_data.get('firstname')
        e_lastname = emergency_contact.cleaned_data.get('lastname')

        if e_firstname == billing_member.firstname \
                and e_lastname == billing_member.lastname:
            return True

        return False

    def referent_is_emergency_contact(self):
        emergency_contact = self.form_dict['emergency_contact']
        referent_information = self.form_dict['referent_information']

        e_firstname = emergency_contact.cleaned_data.get('firstname')
        e_lastname = emergency_contact.cleaned_data.get('lastname')

        r_firstname = referent_information.cleaned_data.get("firstname")
        r_lastname = referent_information.cleaned_data.get("lastname")

        if e_firstname == r_firstname and e_lastname == r_lastname:
            return True
        return False

    def referent_is_billing_member(self):
        referent_information = self.form_dict['referent_information']
        payment_information = self.form_dict['payment_information']

        r_firstname = referent_information.cleaned_data.get("firstname")
        r_lastname = referent_information.cleaned_data.get("lastname")

        p_firstname = payment_information.cleaned_data.get('firstname')
        p_lastname = payment_information.cleaned_data.get('lastname')

        if r_firstname == p_firstname and r_lastname == p_lastname:
            return True
        return False


class ClientList(generic.ListView):
    # Display the list of clients
    model = Client
    template_name = 'client/list.html'
    context_object_name = 'clients'
    paginate_by = 21

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClientList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        uf = ClientFilter(self.request.GET)
        return uf.qs

        # The queryset must be client

    def get_context_data(self, **kwargs):
        uf = ClientFilter(self.request.GET, queryset=self.get_queryset())

        context = super(ClientList, self).get_context_data(**kwargs)

        # Here you add some variable of context to display on template
        context['myVariableOfContext'] = 0
        context['filter'] = uf
        context['display'] = self.request.GET.get('display', 'block')
        text = ''
        count = 0
        for getVariable in self.request.GET:
            if getVariable == "display" or getVariable == "page":
                continue
            for getValue in self.request.GET.getlist(getVariable):
                if count == 0:
                    text += "?" + getVariable + "=" + getValue
                else:
                    text += "&" + getVariable + "=" + getValue
                count += 1

        text = text + "?" if count == 0 else text + "&"
        context['get'] = text

        return context

    def get(self, request, **kwargs):

        self.format = request.GET.get('format', False)

        if self.format == 'csv':
            return ExportCSV(
                self, self.get_queryset()
            )

        return super(ClientList, self).get(request, **kwargs)


def ExportCSV(self, queryset):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] =\
        'attachment; filename=client_export.csv'
    writer = csv.writer(response, csv.excel)
    writer.writerow([
        "ID",
        "Client Firstname",
        "Client Lastname",
        "Client Status",
        "Client Alert",
        "Client Gender",
        "Client Birthdate",
        "Client Delivery",
        "Client Home Phone",
        "Client Cell Phone",
        "Client Work Phone",
        "Client Email",
        "Client Street",
        "Client Apartment",
        "Client City",
        "Client Postal Code",
        "Client Route",
        "Client Billing Type",
        "Billing Firstname",
        "Billing Lastname",
        "Billing Street",
        "Billing Apartment",
        "Billing City",
        "Billing Postal Code",
        "Emergency Contact Firstname",
        "Emergency Contact Lastname",
        "Emergency Contact Home Phone",
        "Emergency Contact Cell Phone",
        "Emergency Contact Work Phone",
        "Emergency Contact Email",
        "Emergency Contact Relationship",
        "Meal Default",
    ])

    for obj in queryset:
        if obj.route is None:
            route = ""

        else:
            route = obj.route.name

        writer.writerow([
            obj.id,
            obj.member.firstname,
            obj.member.lastname,
            obj.status,
            obj.alert,
            obj.gender,
            obj.birthdate,
            obj.delivery_type,
            obj.member.home_phone,
            obj.member.cell_phone,
            obj.member.work_phone,
            obj.member.email,
            obj.member.address.street,
            obj.member.address.apartment,
            obj.member.address.city,
            obj.member.address.postal_code,
            route,
            obj.billing_payment_type,
            obj.billing_member.firstname,
            obj.billing_member.lastname,
            obj.billing_member.address.street,
            obj.billing_member.address.apartment,
            obj.billing_member.address.city,
            obj.billing_member.address.postal_code,
            obj.emergency_contact.firstname,
            obj.emergency_contact.lastname,
            obj.emergency_contact.home_phone,
            obj.emergency_contact.cell_phone,
            obj.emergency_contact.work_phone,
            obj.emergency_contact.email,
            obj.emergency_contact_relationship,
            obj.meal_default_week,
        ])

    return response


class ClientInfoView(generic.DetailView):
    # Display detail of one client
    model = Client
    template_name = 'client/view/information.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClientInfoView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ClientInfoView, self).get_context_data(**kwargs)
        context['active_tab'] = 'information'
        context['client_status'] = Client.CLIENT_STATUS
        """
        Here we need to add some variable of context to send to template :
         1 - A string active_tab who can be:
            'info'
            'referent'
            'address'
            'payment'
            'allergies'
            'preferences'
        """
        context['myVariableOfContext'] = 0

        return context


class ClientReferentView(generic.DetailView):
    # Display detail of one client
    model = Client
    template_name = 'client/view/referent.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClientReferentView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ClientReferentView, self).get_context_data(**kwargs)
        context['active_tab'] = 'referent'
        context['client_status'] = Client.CLIENT_STATUS
        """
        Here we need to add some variable of context to send to template :
         1 - A string active_tab who can be:
            'info'
            'referent'
            'address'
            'payment'
            'allergies'
            'preferences'
        """
        context['myVariableOfContext'] = 0

        return context


class ClientAddressView(generic.DetailView):
    # Display detail of one client
    model = Client
    template_name = 'client/view/address.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClientAddressView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ClientAddressView, self).get_context_data(**kwargs)

        """
        Here we need to add some variable of context to send to template :
         1 - A string active_tab who can be:
            'info'
            'referent'
            'address'
            'payment'
            'allergies'
            'preferences'
        """
        context['myVariableOfContext'] = 0

        return context


class ClientPaymentView(generic.DetailView):
    # Display detail of one client
    model = Client
    template_name = 'client/view/payment.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClientPaymentView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ClientPaymentView, self).get_context_data(**kwargs)
        context['active_tab'] = 'billing'
        context['client_status'] = Client.CLIENT_STATUS
        """
        Here we need to add some variable of context to send to template :
         1 - A string active_tab who can be:
            'info'
            'referent'
            'address'
            'payment'
            'allergies'
            'preferences'
        """
        context['myVariableOfContext'] = 0

        return context


class ClientAllergiesView(generic.DetailView):
    # Display detail of one client
    model = Client
    template_name = 'client/view/allergies.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClientAllergiesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ClientAllergiesView, self).get_context_data(**kwargs)
        context['active_tab'] = 'prefs'
        context['client_status'] = Client.CLIENT_STATUS
        if self.object.meal_default_week:
            context['meal_default'] = parse_json(self.object.meal_default_week)
        else:
            context['meal_default'] = []

        """
        Here we need to add some variable of context to send to template :
         1 - A string active_tab who can be:
            'info'
            'referent'
            'address'
            'payment'
            'allergies'
            'preferences'
        """
        context['myVariableOfContext'] = 0

        return context


class ClientNotesView(generic.DetailView):
    # Display detail of one client
    model = Client
    template_name = 'client/view/notes.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClientNotesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ClientNotesView, self).get_context_data(**kwargs)
        context['active_tab'] = 'notes'
        context['notes'] = NoteClientFilter(
            self.request.GET, queryset=self.object.notes).qs

        uf = NoteClientFilter(self.request.GET, queryset=self.object.notes)
        context['filter'] = uf

        return context


def note_add(request):
    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            model_instance = form.save(commit=False)
            model_instance.author = request.user
            model_instance.save()
            return render(request, 'notes/add.html', {'form': form})
    else:
        form = NoteForm()

    return render(request, 'notes/add.html', {'form': form})


def parse_json(meals):
    meal_default = []

    for meal in meals:
        if meals[meal] is not None:
            meal_default.append(meal + ": " + str(meals[meal]))

    return meal_default


class ClientDetail(generic.DetailView):
    # Display detail of one client
    model = Client
    template_name = 'client/view.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClientDetail, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ClientDetail, self).get_context_data(**kwargs)
        context['notes'] = list(Note.objects.all())
        if self.object.meal_default_week:
            context['meal_default'] = parse_json(self.object.meal_default_week)
        else:
            context['meal_default'] = []
        return context


class ClientOrderList(generic.DetailView):
    # Display the list of clients
    model = Client
    template_name = 'client/orders_list.html'

    def get_context_data(self, **kwargs):

        context = super(ClientOrderList, self).get_context_data(**kwargs)
        context['orders'] = self.object.orders
        context['client_status'] = Client.CLIENT_STATUS
        context['active_tab'] = 'orders'
        return context


class ClientPreferencesView(generic.DetailView):
    # Display preferences of one client
    model = Client
    template_name = 'client/view/preferences.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ClientPreferencesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ClientPreferencesView, self).get_context_data(**kwargs)
        context['meal_default'] = self.object.meal_default_week

        """
        Here we need to add some variable of context to send to template :
         1 - A string active_tab who can be:
            'info'
            'referent'
            'address'
            'payment'
            'allergies'
            'preferences'
        """
        context['myVariableOfContext'] = 0

        return context


class MemberUpdate(generic.UpdateView):
    # Display the form to update a member
    model = Member
    template_name = "client/update.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # Here you need to check if the client exist
        # You can use for example get_object_or_404()
        # note: self.kwargs["pk"] is the ID of the client given by the urls.py

        return super(MemberUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        # Here you redirect to the next page
        # You can use for example reverse_lazy()

        return 0

    def get_context_data(self, **kwargs):
        context = super(MemberUpdate, self).get_context_data(**kwargs)

        """
        Here we need to add some variable of context to send to template :
         1 - A string active_tab who can be:
            'info'
            'referent'
            'address'
            'payment'
            'allergies'
            'preferences'
        """
        context['myVariableOfContext'] = 0

        return context


class ClientAllergiesUpdate(generic.UpdateView):
    # Display the form to update allergies of a client
    model = Client
    template_name = "client/update.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # Here you need to check if the client exist
        # You can use for example get_object_or_404()
        # note: self.kwargs["pk"] is the ID of the client given by the urls.py

        return super(ClientAllergiesUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        # Here you redirect to the next page
        # You can use for example reverse_lazy()

        return 0

    def get_context_data(self, **kwargs):
        context = super(ClientAllergiesUpdate, self).get_context_data(**kwargs)

        """
        Here we need to add some variable of context to send to template :
         1 - A string active_tab who can be:
            'info'
            'referent'
            'address'
            'payment'
            'allergies'
            'preferences'
        """
        context['myVariableOfContext'] = 0

        return context


class ClientPreferencesUpdate(generic.UpdateView):
    # Display the form to update preference of a client
    model = Client
    template_name = "client/update.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # Here you need to check if the client exist
        # You can use for example get_object_or_404()
        # note: self.kwargs["pk"] is the ID of the client given by the urls.py

        return super(ClientPreferencesUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        # Here you redirect to the next page
        # You can use for example reverse_lazy()

        return 0

    def get_context_data(self, **kwargs):
        context = super(ClientPreferencesUpdate, self).\
            get_context_data(**kwargs)

        """
        Here we need to add some variable of context to send to template :
         1 - A string active_tab who can be:
            'info'
            'referent'
            'address'
            'payment'
            'allergies'
            'preferences'
        """
        context['myVariableOfContext'] = 0

        return context


class SearchMembers(generic.View):

    def get(self, request):
        if request.is_ajax():
            q = self.request.GET.get('name', '')
            name_contains = Q()
            firstname_contains = Q(
                firstname__icontains=q
            )
            lastname_contains = Q(
                lastname__icontains=q
            )
            name_contains |= firstname_contains | lastname_contains
            members = Member.objects.filter(name_contains)[:20]
            results = []
            for m in members:
                name = '[' + str(m.id) + '] ' + m.firstname + ' ' + m.lastname
                results.append({'title': name})
            data = {
                'success': True,
                'results': results
            }
        else:
            data = {'success': False}

        return JsonResponse(data)


def geolocateAddress(request):
            # do something with the your data
    if request.method == 'POST':
        lat = request.POST['lat']
        long = request.POST['long']

    # just return a JsonResponse
    return JsonResponse({'latitude': lat, 'longtitude': long})


def change_status(request, id):
    if request.method == "POST":
        client = get_object_or_404(Client, pk=id)
        status = request.POST.get('status')
        client.status = status
        client.save()

        # just return a JsonResponse
        return JsonResponse({'status': 200})


def clientStatusScheduler(request, pk):
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'client/modal/change_status.html', {
        'client': client,
        'client_status': Client.CLIENT_STATUS,
        'status_to': request.GET.get('status', Client.PAUSED),
    })


class DeleteRestriction(generic.DeleteView):
    model = Restriction
    success_url = reverse_lazy('member:list')


class DeleteClientOption(generic.DeleteView):
    model = Client_option
    success_url = reverse_lazy('member:list')


class DeleteIngredientToAvoid(generic.DeleteView):
    model = Client_avoid_ingredient
    success_url = reverse_lazy('member:list')


class DeleteComponentToAvoid(generic.DeleteView):
    model = Client_avoid_component
    success_url = reverse_lazy('member:list')
