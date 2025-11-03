# BOUNDARY: All HTTP routes and request handling
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from types import SimpleNamespace

from ..control.auth_controller import AuthController
from ..control.user_admin_controller import UserAdminController
from ..control.csr_controller import CSRController
from ..control.pin_controller import PINController
from ..control.pm_controller import PMController  # <-- use Control, not Entity

boundary_bp = Blueprint('boundary', __name__)

# ---------- Auth ----------
@boundary_bp.route('/', methods=['GET'])
def home():
    """Render the login page."""
    profiles = UserAdminController.get_active_profiles()
    return render_template('auth.html', page='login', body_class='bg login', profiles=profiles)


@boundary_bp.route('/login', methods=['POST'])
def login():
    """Handle user login and redirect by role."""
    role = request.form.get('role')
    username = request.form.get('username')
    password = request.form.get('password')
    user = AuthController.login(role, username, password)
    if user:
        session['user_id'] = user.id
        session['role'] = user.profile.name if getattr(user, 'profile', None) else ''
        session['username'] = user.username
        if session['role'] == 'User Admin':
            return redirect(url_for('boundary.admin_new_user'))
        elif session.get('role') == 'CSR Representative':
            return redirect(url_for('boundary.csr_dashboard'))
        elif session.get('role') == 'Person in Need':
            return redirect(url_for('boundary.pin_dashboard'))
        elif session.get('role') == 'Platform Manager':
            return redirect(url_for('boundary.pm_dashboard'))
    flash('Invalid credentials or suspended account.')
    return redirect(url_for('boundary.home'))


@boundary_bp.route('/logout')
def logout():
    """Clear session and render logout page."""
    username = session.get('username', '')
    AuthController.logout()
    return render_template('auth.html', page='logout', username=username, body_class='bg login')


# ---------- User Admin ----------
@boundary_bp.route('/admin')
def admin_dashboard():
    AuthController.require_role('User Admin')
    # keep a simple redirect to the list
    return redirect(url_for('boundary.admin_users'))


@boundary_bp.route('/admin/users')
def admin_users():
    """Users page with Accounts/Profiles filter + search + pagination."""
    AuthController.require_role('User Admin')
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    view_type = request.args.get('type', 'accounts')  # 'accounts' or 'profiles'
    pag = UserAdminController.search_users(q=q, user_type=view_type, page=page, per_page=per_page)
    return render_template(
        'user_admin.html',
        view='users',
        users=pag['items'],
        q=q,
        page=pag['page'],
        per_page=pag['per_page'],
        total=pag['total'],
        pages=pag['pages'],
        type=view_type,
        body_class='bg'
    )


@boundary_bp.route('/admin/users/new', methods=['GET'])
def admin_new_user():
    AuthController.require_role('User Admin')
    profiles = UserAdminController.get_active_profiles()
    return render_template('user_admin.html', view='create', profiles=profiles, body_class='bg create')


@boundary_bp.route('/admin/users/create', methods=['POST'])
def admin_create_user():
    AuthController.require_role('User Admin')
    user_type = (request.form.get('user_type') or '').lower()
    if user_type == 'profile':
        # create a role/profile (name supplied in full_name field)
        name = (request.form.get('full_name') or '').strip()
        ok, msg = UserAdminController.create_profile(name=name, active=True)
        flash(msg)
        return redirect(url_for('boundary.admin_users', type='profiles'))
    # otherwise create a user account
    # split submitted full name into first/last
    full_name = (request.form.get('full_name') or '').strip()
    first_name = ''
    last_name = ''
    if full_name:
        parts = full_name.split(None, 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''
    ok, msg = UserAdminController.create_user_account(
        first_name=first_name,
        last_name=last_name,
        email=request.form.get('email'),
        phone=request.form.get('phone'),
        username=request.form.get('username'),
        password=request.form.get('password'),
    )
    flash(msg)
    # return to accounts list
    return redirect(url_for('boundary.admin_users', type='accounts'))


@boundary_bp.route('/admin/users/<int:user_id>/edit', methods=['GET'])
def admin_edit_user(user_id):
    AuthController.require_role('User Admin')
    user = UserAdminController.get_user_by_id(user_id)
    if not user:
        flash('User not found.')
        return redirect(url_for('boundary.admin_users'))
    profiles = UserAdminController.get_active_profiles()
    return render_template('user_admin.html', view='edit', user=user, profiles=profiles, body_class='bg create')


@boundary_bp.route('/admin/users/<int:user_id>/update', methods=['POST'])
def admin_update_user(user_id):
    AuthController.require_role('User Admin')
    # split full name into first/last
    full_name = (request.form.get('full_name') or '').strip()
    first_name = ''
    last_name = ''
    if full_name:
        parts = full_name.split(None, 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

    ok, msg = UserAdminController.update_user_with_profile(
        user_id=user_id,
        profile_name=request.form.get('role'),
        username=request.form.get('username'),
        password=request.form.get('password'),
        # this is here to fix the suspension of account when updating a user.
        active=request.form.get('active'),
        first_name=first_name,
        last_name=last_name,
        email=request.form.get('email'),
        phone=request.form.get('phone'),
    )
    flash(msg)
    return redirect(url_for('boundary.admin_users'))


@boundary_bp.route('/admin/users/<int:user_id>/suspend', methods=['POST'])
def admin_suspend_user(user_id):
    AuthController.require_role('User Admin')
    UserAdminController.suspend_user(user_id)
    flash('User suspended.')
    return redirect(url_for('boundary.admin_users'))


@boundary_bp.route('/admin/users/<int:user_id>/activate', methods=['POST'])
def admin_activate_user(user_id):
    AuthController.require_role('User Admin')
    UserAdminController.activate_user(user_id)
    flash('User activated.')
    return redirect(url_for('boundary.admin_users'))


# ---------- Profile management (User Admin) ----------
@boundary_bp.route('/admin/profiles/<int:profile_id>/edit')
def admin_edit_profile(profile_id):
    AuthController.require_role('User Admin')
    profile = UserAdminController.get_profile_by_id(profile_id)
    if not profile:
        flash('Profile not found.')
        return redirect(url_for('boundary.admin_users', type='profiles'))
    return render_template(
        'user_admin.html',
        view='edit_profile',
        profile=profile,
        body_class='bg create'
    )


@boundary_bp.route('/admin/profiles/<int:profile_id>/update', methods=['POST'])
def admin_update_profile(profile_id):
    AuthController.require_role('User Admin')
    ok, msg = UserAdminController.update_profile(
        profile_id=profile_id,
        name=request.form.get('full_name'),
        active=request.form.get('active'),
    )
    flash(msg)
    return redirect(url_for('boundary.admin_users', type='profiles'))


@boundary_bp.route('/admin/profiles/<int:profile_id>/suspend', methods=['POST'])
def admin_suspend_profile(profile_id):
    AuthController.require_role('User Admin')
    UserAdminController.suspend_profile(profile_id)
    flash('Profile suspended.')
    return redirect(url_for('boundary.admin_users', type='profiles'))


@boundary_bp.route('/admin/profiles/<int:profile_id>/activate', methods=['POST'])
def admin_activate_profile(profile_id):
    AuthController.require_role('User Admin')
    UserAdminController.activate_profile(profile_id)
    flash('Profile activated.')
    return redirect(url_for('boundary.admin_users', type='profiles'))


# ---------- CSR ----------
@boundary_bp.route('/csr')
def csr_dashboard():
    AuthController.require_role('CSR Representative')
    categories = CSRController.get_categories()
    qcat = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    pag = CSRController.search_requests(category_id=qcat, page=page, per_page=per_page)
    requests_list = pag['items']
    full_shortlist = CSRController.get_shortlist()
    history_pag = CSRController.history()
    if isinstance(history_pag, dict):
        history_items = history_pag.get('items', [])
    else:
        history_items = history_pag or []
    saved_ids = {s.request_id for s in (full_shortlist or [])}
    return render_template(
        'csr_rep.html',
        view='dashboard',
        categories=categories,
        requests=requests_list,
        saved_ids=saved_ids,
        category_id=qcat,
        page=pag['page'],
        per_page=pag['per_page'],
        total=pag['total'],
        pages=pag['pages'],
        shortlist=(full_shortlist or [])[:5],
        history_preview=(history_items or [])[:5]
    )


@boundary_bp.route('/csr/request/<int:req_id>/save', methods=['POST'])
def csr_save(req_id):
    AuthController.require_role('CSR Representative')
    CSRController.save_request(req_id)
    flash('Saved to shortlist.')
    return redirect(url_for('boundary.csr_dashboard'))


@boundary_bp.route('/csr/request/<int:req_id>/unsave', methods=['POST'])
def csr_unsave(req_id):
    AuthController.require_role('CSR Representative')
    ok = CSRController.remove_request(req_id)
    if ok:
        flash('Removed from shortlist.')
    else:
        flash('Not in shortlist.')
    return redirect(url_for('boundary.csr_dashboard'))


@boundary_bp.route('/csr/history')
def csr_history():
    AuthController.require_role('CSR Representative')
    categories = CSRController.get_categories()
    category_id = request.args.get('category_id', type=int)
    start = request.args.get('start')
    end = request.args.get('end')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    pag = CSRController.history(category_id=category_id, start=start, end=end, page=page, per_page=per_page)
    items = pag['items']
    return render_template(
        'csr_rep.html',
        view='history',
        categories=categories,
        items=items,
        page=pag['page'],
        per_page=pag['per_page'],
        total=pag['total'],
        pages=pag['pages'],
        category_id=category_id,
        start=start,
        end=end,
    )


@boundary_bp.route('/csr/request/<int:req_id>')
def csr_request(req_id):
    AuthController.require_role('CSR Representative')
    categories = CSRController.get_categories()
    r = CSRController.get_request(req_id)
    if not r:
        flash('Request not found or not available.')
        return redirect(url_for('boundary.csr_dashboard'))
    saved = CSRController.is_saved_by(req_id)
    return render_template('csr_rep.html', view='detail', request_item=r, categories=categories, saved=saved)


@boundary_bp.route('/csr/request/<int:req_id>/accept', methods=['POST'])
def csr_accept(req_id):
    AuthController.require_role('CSR Representative')
    ok = CSRController.accept_request(req_id)
    if ok:
        flash('You have accepted the request. The PIN will see your name once the request is marked completed.')
    else:
        flash('Unable to accept the request (it may already be accepted or closed).')
    return redirect(url_for('boundary.csr_request', req_id=req_id))


@boundary_bp.route('/csr/shortlist')
def csr_shortlist():
    AuthController.require_role('CSR Representative')
    categories = CSRController.get_categories()
    sq = request.args.get('sq','').strip()
    shortlist = CSRController.search_shortlist(sq) if sq else CSRController.get_shortlist()
    full_shortlist = CSRController.get_shortlist()
    saved_ids = {s.request_id for s in (full_shortlist or [])}
    return render_template('csr_rep.html', view='shortlist', categories=categories, shortlist=shortlist, saved_ids=saved_ids, shortlist_q=sq)


# ---------- PIN ----------
@boundary_bp.route('/pin')
def pin_dashboard():
    AuthController.require_role('Person in Need')
    categories = PINController.get_categories()
    q = request.args.get('q','').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    pag = PINController.list_my_requests(q, page=page, per_page=per_page)
    reqs = pag['items']
    history_preview = PINController.history() or []
    return render_template('pin.html', view='dashboard', categories=categories, reqs=reqs, q=q, page=pag['page'], per_page=pag['per_page'], total=pag['total'], pages=pag['pages'], history_preview=(history_preview or [])[:5])


@boundary_bp.route('/pin/request/new', methods=['GET'])
def pin_new_req():
    AuthController.require_role('Person in Need')
    categories = PINController.get_categories()
    return render_template('pin.html', view='create', categories=categories)


# PIN: CRUD for requests
@boundary_bp.route('/pin/request/create', methods=['POST'])
def pin_create_req():
    AuthController.require_role('Person in Need')
    ok, msg = PINController.create_request(
        title=request.form.get('title'),
        description=request.form.get('description'),
        category_id=request.form.get('category_id')
    )
    flash(msg)
    return redirect(url_for('boundary.pin_dashboard'))


@boundary_bp.route('/pin/request/<int:req_id>/update', methods=['POST'])
def pin_update_req(req_id):
    AuthController.require_role('Person in Need')
    next_url = request.form.get('next') or url_for('boundary.pin_dashboard')

    ok, msg = PINController.update_request(
        req_id,
        title=request.form.get('title'),
        description=request.form.get('description'),
        category_id=request.form.get('category_id'),
        status=request.form.get('status') or 'open'
    )
    if ok:
        flash(msg)
        return redirect(next_url)
    # re-render the edit form with submitted values so user can correct
    flash(msg)
    categories = PINController.get_categories()
    # recreate a lightweight request object to fill the form and include current views_count
    cat_raw = request.form.get('category_id')
    try:
        cat_val = int(cat_raw) if cat_raw else None
    except (TypeError, ValueError):
        cat_val = None
    # fetch existing record to show accurate views_count if available
    existing = PINController.get_request(req_id)
    views = existing.views_count if existing else 0
    req_obj = SimpleNamespace(
        id=req_id,
        title=(request.form.get('title') or '').strip(),
        description=(request.form.get('description') or ''),
        category_id=cat_val,
        status=request.form.get('status') or 'open',
        views_count=views,
    )
    return render_template('pin.html', view='edit', req=req_obj, categories=categories, next=next_url, page=request.form.get('page', 1), per_page=request.form.get('per_page', 12), q=request.form.get('q',''))


@boundary_bp.route('/pin/request/<int:req_id>/edit', methods=['GET'])
def pin_edit_req(req_id):
    AuthController.require_role('Person in Need')
    r = PINController.get_request(req_id)
    if not r:
        flash('Request not found or permission denied.')
        return redirect(url_for('boundary.pin_dashboard'))
    categories = PINController.get_categories()
    # preserve caller pagination/search via query params and expose a `next` URL
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    q = request.args.get('q','').strip()
    next_url = request.args.get('next') or url_for('boundary.pin_dashboard', page=page, per_page=per_page, q=q)
    return render_template('pin.html', view='edit', req=r, categories=categories, next=next_url, page=page, per_page=per_page, q=q)


@boundary_bp.route('/pin/request/<int:req_id>/delete', methods=['POST'])
def pin_delete_req(req_id):
    AuthController.require_role('Person in Need')
    # preserve caller pagination/search via optional 'next' hidden field
    next_url = request.form.get('next') or url_for('boundary.pin_dashboard')
    ok = PINController.delete_request(req_id)
    if ok:
        flash('Request deleted.')
    else:
        flash('Request not found or permission denied.')
    return redirect(next_url)


@boundary_bp.route('/pin/history')
def pin_history():
    AuthController.require_role('Person in Need')
    categories = PINController.get_categories()
    category_id = request.args.get('category_id', type=int)
    start = request.args.get('start')
    end = request.args.get('end')
    q = request.args.get('q','').strip()
    items = PINController.history(category_id=category_id, start=start, end=end, q=q)
    return render_template('pin.html', view='history', categories=categories, items=items, category_id=category_id, start=start, end=end, q=q)


# ---------- Platform Manager ----------
@boundary_bp.route('/pm')
def pm_dashboard():
    AuthController.require_role('Platform Manager')
    q = request.args.get('q','').strip()
    categories = PMController.search_categories(q)
    return render_template('pm.html', view='dashboard', categories=categories, q=q)


@boundary_bp.route('/pm/category/create', methods=['POST'])
def pm_create_cat():
    AuthController.require_role('Platform Manager')
    PMController.create_category(request.form.get('name'))
    flash('Category created.')
    return redirect(url_for('boundary.pm_dashboard'))


@boundary_bp.route('/pm/category/<int:cat_id>/update', methods=['POST'])
def pm_update_cat(cat_id):
    AuthController.require_role('Platform Manager')
    PMController.update_category(cat_id, request.form.get('name'))
    flash('Category updated.')
    return redirect(url_for('boundary.pm_dashboard'))


@boundary_bp.route('/pm/category/<int:cat_id>/delete', methods=['POST'])
def pm_delete_cat(cat_id):
    AuthController.require_role('Platform Manager')
    PMController.delete_category(cat_id)
    flash('Category deleted.')
    return redirect(url_for('boundary.pm_dashboard'))


@boundary_bp.route('/pm/reports')
def pm_reports():
    AuthController.require_role('Platform Manager')
    scope = request.args.get('scope', 'daily')
    data = PMController.generate_report(scope)
    return render_template('pm.html', view='reports', scope=scope, data=data)
