from django.contrib.auth import authenticate, get_user_model, login, logout
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from decimal import Decimal
from datetime import timedelta
import mimetypes
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from .models import (Brand, ContactMessage, CustomerProfile, Device, Product, Promotion,
                     RepairInvoice, RepairPhoto, RepairQuote, RepairRequest, RepairService, RepairUpdate,
                     SupportConversation, SupportMessage, Testimonial)
from .form import (ChatMessageForm, ContactMessageForm, CustomerProfileForm, DeviceForm, RepairBookingForm,
                   RepairTrackingForm, UserLoginForm, UserRegistrationForm)


# Create your views here.

def home(request):
    featured_products = Product.objects.select_related('brand').order_by('-pk')[:4]
    supported_phone_brands = Brand.objects.filter(name__in=['Samsung', 'Apple', 'TECNO', 'Infinix', 'OPPO', 'vivo', 'realme']).order_by('name')
    now = timezone.now()
    promotions = Promotion.objects.filter(is_active=True).filter(
        Q(starts_at__isnull=True) | Q(starts_at__lte=now),
        Q(ends_at__isnull=True) | Q(ends_at__gte=now),
    )[:3]
    services = RepairService.objects.filter(is_active=True)[:6]
    testimonials = Testimonial.objects.filter(is_published=True)[:3]
    return render(request, 'landing.html', {
        'featured_products': featured_products,
        'repair_services': services,
        'promotions': promotions,
        'testimonials': testimonials,
        'supported_phone_brands': supported_phone_brands,
    })





def login_view(request):
    # get the login form
    login_form = UserLoginForm(request.POST or None)

    if request.method == 'POST' and login_form.is_valid():
        username = login_form.cleaned_data['username']
        password = login_form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is None and '@' in username:
            matches = get_user_model().objects.filter(email__iexact=username)
            if matches.count() == 1:
                user = authenticate(request, username=matches.first().get_username(), password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect('home')
        else:
            login_form.add_error(None, 'Invalid username or password.')

    return render(request, 'login.html', {'form': login_form})


def signup_view(request):
    form = UserRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(next_url)
        return redirect('home')
    return render(request, 'signup.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('home')



def product_list(request):
    query = request.GET.get('q', '').strip()[:100]
    products = Product.objects.all().order_by('name', 'pk')
    selected_brand = None
    brand_id = request.GET.get('brand', '')
    if brand_id.isdecimal() and len(brand_id) <= 19:
        try:
            selected_brand = Brand.objects.filter(pk=int(brand_id)).first()
        except (OverflowError, ValueError):
            selected_brand = None
    if selected_brand:
        products = products.filter(brand=selected_brand)
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(brand__name__icontains=query)
        )

    page = Paginator(products, 12).get_page(request.GET.get('page'))
    return render(request, 'products.html', {
        'page': page,
        'query': query,
        'selected_brand': selected_brand,
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product_detail.html', {'product': product})

def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('product_detail', product_id=product_id)
    product = get_object_or_404(Product, pk=product_id)
    try:
        quantity = int(request.POST.get('quantity', '1'))
    except (TypeError, ValueError):
        quantity = 0
    if not 1 <= quantity <= 99:
        from django.contrib import messages
        messages.error(request, 'Choose a quantity from 1 to 99.')
        return redirect('product_detail', product_id=product_id)
    cart = request.session.get('cart', {})
    key = str(product.pk)
    cart[key] = min(99, int(cart.get(key, 0)) + quantity)
    request.session['cart'] = cart
    from django.contrib import messages
    messages.success(request, f'{product.name} added to your cart.')
    return redirect('cart')


def view_cart(request):
    from django.contrib import messages
    cart = request.session.get('cart', {})
    if request.method == 'POST':
        product_id = request.POST.get('product_id', '')
        action = request.POST.get('action', '')
        key = str(product_id)
        if key not in cart:
            messages.error(request, 'That item is no longer in your cart.')
            return redirect('cart')
        if action == 'remove':
            cart.pop(key, None)
            messages.success(request, 'Item removed from your cart.')
        elif action == 'update':
            try:
                quantity = int(request.POST.get('quantity', '0'))
            except (TypeError, ValueError):
                quantity = 0
            if not 1 <= quantity <= 99:
                messages.error(request, 'Choose a quantity from 1 to 99.')
            else:
                cart[key] = quantity
                messages.success(request, 'Cart updated.')
        request.session['cart'] = cart
        return redirect('cart')

    items = []
    valid_cart = {}
    for key, quantity in cart.items():
        try:
            product_id, quantity = int(key), int(quantity)
        except (TypeError, ValueError):
            continue
        if not 1 <= quantity <= 99:
            continue
        product = Product.objects.filter(pk=product_id).first()
        if product:
            line_total = product.price * quantity
            items.append({'product': product, 'quantity': quantity, 'line_total': line_total})
            valid_cart[str(product_id)] = quantity
    if valid_cart != cart:
        request.session['cart'] = valid_cart
    total = sum((item['line_total'] for item in items), Decimal('0.00'))
    return render(request, 'cart.html', {'cart_items': items, 'cart_total': total})


def drivers(request):
    return render(request, 'drivers.html')


def diagnose(request):
    devices = (
        {
            'id': 'phone',
            'name': 'Phone',
            'description': 'Charging, screen, or heat problems',
            'issues': (
                {
                    'id': 'power',
                    'title': 'Won’t turn on or charge',
                    'parts_query': 'charger',
                    'steps': (
                        'Try a wall outlet that you know works and a compatible charger and cable.',
                        'Check the charger and cable from the outside. Stop using them if they are damaged, unusually hot, or loose.',
                        'Leave the phone connected to the known-good charger for 30 minutes, then try turning it on.',
                        'If it remains unresponsive, stop and have the phone checked by a qualified repair service. Do not open it.',
                    ),
                },
                {
                    'id': 'screen',
                    'title': 'Screen is blank or unresponsive',
                    'parts_query': 'screen',
                    'steps': (
                        'If the phone is on, increase screen brightness and check whether it responds to the power button.',
                        'If the screen is dry and undamaged, gently wipe it with a soft, dry cloth.',
                        'Restart the phone using its normal power-button method.',
                        'If the screen is cracked, lifting, hot, or still unresponsive, stop using it and arrange a repair.',
                    ),
                },
                {
                    'id': 'heat',
                    'title': 'Phone is getting unusually hot',
                    'parts_query': '',
                    'steps': (
                        'Disconnect the charger if it is safe to do so, close demanding apps, and remove the case.',
                        'Turn the phone off and let it cool on a dry, hard surface away from sunlight.',
                        'Do not put it in a refrigerator, use water, or continue charging it while it is hot.',
                        'If it becomes hot again while idle, stop using it and arrange a professional inspection.',
                    ),
                },
            ),
        },
        {
            'id': 'laptop',
            'name': 'Laptop',
            'description': 'Power, performance, or heat problems',
            'issues': (
                {
                    'id': 'power',
                    'title': 'Laptop won’t turn on',
                    'parts_query': 'laptop charger',
                    'steps': (
                        'Check that the wall outlet works and the charger is connected securely at both ends.',
                        'Disconnect accessories such as USB drives and docks, then try the power button once.',
                        'Inspect the charger externally. Do not use it if the cable or plug is damaged or unusually hot.',
                        'If there is still no response, stop and contact a qualified repair service. Do not open the laptop.',
                    ),
                },
                {
                    'id': 'slow',
                    'title': 'Laptop is running slowly',
                    'parts_query': '',
                    'drivers': True,
                    'steps': (
                        'Save your work and restart the laptop.',
                        'Close apps and browser tabs you are not using, then check whether performance improves.',
                        'Check that the operating system has enough free storage and install updates offered by its official update tool.',
                        'For driver updates, use the laptop maker’s official support page for your exact model.',
                    ),
                },
                {
                    'id': 'heat',
                    'title': 'Laptop is overheating or noisy',
                    'parts_query': '',
                    'steps': (
                        'Save your work and shut the laptop down if it is very hot.',
                        'Place it on a hard, flat surface and make sure the external vents are not blocked.',
                        'After it cools, wipe dust from the outside vents with a dry, soft cloth. Do not open the case.',
                        'If it overheats again, shuts down, or smells burnt, stop using it and arrange a repair.',
                    ),
                },
            ),
        },
        {
            'id': 'desktop',
            'name': 'Desktop PC',
            'description': 'Power, display, or heat problems',
            'issues': (
                {
                    'id': 'power',
                    'title': 'PC won’t turn on',
                    'parts_query': 'power cable',
                    'steps': (
                        'Check the wall outlet with another device and make sure the PC power cable is firmly connected.',
                        'If the PC has an external power switch, check that it is set to on.',
                        'Disconnect nonessential USB accessories and try turning the PC on once.',
                        'Do not open the power supply or computer case. If it remains off, contact a qualified repair service.',
                    ),
                },
                {
                    'id': 'display',
                    'title': 'PC turns on but there is no display',
                    'parts_query': 'display cable',
                    'steps': (
                        'Check that the monitor is powered on and set to the correct input.',
                        'Check that the display cable is firmly connected at the monitor and PC.',
                        'If available, try a known-good cable or another monitor input.',
                        'If the display remains blank, turn the PC off and arrange a qualified inspection rather than opening the case.',
                    ),
                },
                {
                    'id': 'heat',
                    'title': 'PC is overheating or noisy',
                    'parts_query': '',
                    'steps': (
                        'Shut the PC down if it is very hot, making unusual noises, or smells burnt.',
                        'Make sure the outside vents have space around them and are not covered.',
                        'When powered off, wipe dust from external vents with a dry, soft cloth. Do not open the case.',
                        'If overheating continues or a fan appears not to work, arrange a qualified repair.',
                    ),
                },
            ),
        },
    )
    device_id = request.GET.get('device', '')
    selected_device = next((device for device in devices if device['id'] == device_id), None)
    issue_id = request.GET.get('issue', '')
    selected_issue = None
    if selected_device:
        selected_issue = next(
            (issue for issue in selected_device['issues'] if issue['id'] == issue_id),
            None,
        )

    return render(request, 'diagnose.html', {
        'diagnostic_devices': devices,
        'selected_device': selected_device,
        'selected_issue': selected_issue,
    })


@login_required
def profile_view(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    form = CustomerProfileForm(request.POST or None, instance=profile, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your profile was updated.')
        return redirect('profile')
    recent_repairs = request.user.repair_requests.select_related('device__brand', 'service')[:5]
    devices = request.user.devices.select_related('brand')[:5]
    return render(request, 'profile.html', {
        'form': form, 'recent_repairs': recent_repairs, 'devices': devices,
    })


@login_required
def device_list(request):
    devices = request.user.devices.select_related('brand')
    return render(request, 'device_list.html', {'devices': devices})


@login_required
def device_add(request):
    form = DeviceForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        device = form.save(commit=False)
        device.customer = request.user
        device.save()
        messages.success(request, 'Device saved to your account.')
        return redirect('device_list')
    return render(request, 'device_form.html', {'form': form})


@login_required
def device_photo(request, device_id):
    device = get_object_or_404(Device, pk=device_id, customer=request.user)
    if not device.photo:
        from django.http import Http404
        raise Http404
    response = FileResponse(device.photo.open('rb'), content_type=mimetypes.guess_type(device.photo.name)[0] or 'application/octet-stream')
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response


@login_required
def repair_booking(request):
    if not request.user.devices.exists():
        messages.info(request, 'Register your phone before requesting a repair.')
        return redirect('device_add')
    form = RepairBookingForm(request.POST or None, request.FILES or None, customer=request.user)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            repair = form.save(commit=False)
            repair.customer = request.user
            repair.save()
            RepairUpdate.objects.create(
                repair=repair, status=repair.status,
                comment='Repair request received. The team will review the details.',
            )
            for photo in form.cleaned_data['photos']:
                RepairPhoto.objects.create(repair=repair, image=photo)
        messages.success(request, f'Repair request submitted. Reference: {repair.reference}')
        return redirect('repair_detail', reference=repair.reference)
    return render(request, 'repair_booking.html', {'form': form})


@login_required
def repair_list(request):
    repairs = request.user.repair_requests.select_related('device__brand', 'service')
    return render(request, 'repair_list.html', {'repairs': repairs})


@login_required
def repair_detail(request, reference):
    repair = get_object_or_404(
        RepairRequest.objects.select_related('device__brand', 'service').prefetch_related('updates', 'photos', 'quotes__invoice'),
        reference=reference, customer=request.user,
    )
    if request.method == 'POST':
        quote_id = request.POST.get('quote_id', '')
        decision = request.POST.get('decision', '')
        if not quote_id.isdecimal() or len(quote_id) > 19:
            messages.error(request, 'That quotation could not be found.')
            return redirect('repair_detail', reference=repair.reference)
        quote = get_object_or_404(RepairQuote, pk=quote_id, repair=repair, status='pending')
        if decision not in ('approved', 'rejected'):
            messages.error(request, 'Choose approve or reject for this quotation.')
        else:
            quote.status = decision
            quote.responded_at = timezone.now()
            quote.save(update_fields=['status', 'responded_at'])
            if decision == 'approved':
                repair.status = 'approved'
                repair.save(update_fields=['status', 'updated_at'])
                RepairInvoice.objects.get_or_create(quote=quote)
            else:
                repair.status = 'declined'
                repair.save(update_fields=['status', 'updated_at'])
            RepairUpdate.objects.create(
                repair=repair, status=repair.status,
                comment=f'Customer {decision} the quotation.', created_by=request.user,
            )
            messages.success(request, f'Quotation {decision}.')
        return redirect('repair_detail', reference=repair.reference)
    quotes = repair.quotes.prefetch_related('invoice__payments')
    return render(request, 'repair_detail.html', {'repair': repair, 'quotes': quotes})


@login_required
def repair_photo(request, reference, photo_id):
    photo = get_object_or_404(RepairPhoto, pk=photo_id, repair__reference=reference, repair__customer=request.user)
    response = FileResponse(photo.image.open('rb'), content_type=mimetypes.guess_type(photo.image.name)[0] or 'application/octet-stream')
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'private, no-store'
    return response


@login_required
def repair_invoice(request, reference, invoice_number):
    invoice = get_object_or_404(
        RepairInvoice.objects.select_related('quote__repair__device__brand', 'quote__repair__service', 'quote__repair__customer'),
        invoice_number=invoice_number, quote__repair__reference=reference,
        quote__repair__customer=request.user,
    )
    return render(request, 'repair_invoice.html', {'invoice': invoice})


def repair_tracking(request):
    form = RepairTrackingForm(request.GET or None)
    repair = None
    if form.is_valid() and form.cleaned_data.get('reference'):
        reference = form.cleaned_data['reference'].strip().upper()
        repair = RepairRequest.objects.filter(reference=reference).first()
    return render(request, 'repair_tracking.html', {'form': form, 'repair': repair, 'searched': bool(request.GET)})


def contact_view(request):
    form = ContactMessageForm(request.POST or None)
    if request.user.is_authenticated and request.method == 'GET':
        form.initial = {'name': request.user.get_full_name(), 'email': request.user.email}
    if request.method == 'POST' and form.is_valid():
        message = form.save(commit=False)
        if request.user.is_authenticated:
            message.customer = request.user
        message.save()
        messages.success(request, 'Your message has been sent to the support team.')
        return redirect('contact')
    return render(request, 'contact.html', {'form': form})


@login_required
def support_chat(request):
    conversations = request.user.support_conversations.all()
    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            recent_count = SupportMessage.objects.filter(
                conversation__customer=request.user,
                sent_at__gte=timezone.now() - timedelta(minutes=1),
            ).count()
            if recent_count >= 5:
                messages.error(request, 'Please wait a moment before sending another chat message.')
                return render(request, 'support_chat.html', {'conversations': conversations, 'form': form})
            with transaction.atomic():
                conversation = SupportConversation.objects.create(
                    customer=request.user,
                    subject=(request.POST.get('subject', '')[:120].strip() or 'Support chat'),
                )
                SupportMessage.objects.create(
                    conversation=conversation, sender=request.user,
                    body=form.cleaned_data['body'],
                )
            return redirect('support_chat_thread', conversation_id=conversation.pk)
    else:
        form = ChatMessageForm()
    return render(request, 'support_chat.html', {'conversations': conversations, 'form': form})


@login_required
def support_chat_thread(request, conversation_id):
    conversation = get_object_or_404(SupportConversation, pk=conversation_id, customer=request.user)
    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if conversation.status != 'open':
            messages.error(request, 'This support conversation is closed.')
        elif form.is_valid():
            recent_count = SupportMessage.objects.filter(
                conversation__customer=request.user,
                sent_at__gte=timezone.now() - timedelta(minutes=1),
            ).count()
            if recent_count >= 5:
                messages.error(request, 'Please wait a moment before sending another chat message.')
                return redirect('support_chat_thread', conversation_id=conversation.pk)
            SupportMessage.objects.create(
                conversation=conversation, sender=request.user,
                body=form.cleaned_data['body'],
            )
            conversation.save(update_fields=['updated_at'])
        return redirect('support_chat_thread', conversation_id=conversation.pk)
    return render(request, 'support_chat_thread.html', {
        'conversation': conversation,
        'chat_messages': conversation.messages.select_related('sender').all(),
        'form': ChatMessageForm(),
    })


@login_required
def support_chat_messages(request, conversation_id):
    conversation = get_object_or_404(SupportConversation, pk=conversation_id, customer=request.user)
    try:
        after_id = max(0, int(request.GET.get('after', '0')))
    except (TypeError, ValueError):
        after_id = 0
    rows = conversation.messages.filter(pk__gt=after_id).select_related('sender')[:100]
    response = JsonResponse({
        'status': conversation.status,
        'messages': [{
            'id': row.pk,
            'body': row.body,
            'staff': row.is_staff,
            'sender': 'Support team' if row.is_staff else (row.sender.get_full_name() or row.sender.get_username() if row.sender else 'Customer'),
            'sent_at': row.sent_at.isoformat(),
        } for row in rows],
    })
    response['Cache-Control'] = 'no-store'
    return response
