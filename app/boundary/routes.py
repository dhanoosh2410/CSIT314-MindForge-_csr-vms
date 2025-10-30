# BOUNDARY: All HTTP routes and request handling
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..control.auth_controller import AuthController
from ..control.user_admin_controller import UserAdminController
from ..control.csr_controller import CSRController
from ..control.pin_controller import PINController
from ..control.pm_controller import PMController
from ..control.report_controller import ReportController

boundary_bp = Blueprint('boundary', __name__)

# ---------- Auth ----------
@boundary_bp.route('/', methods=['GET'])
def home():
    # render login page
    return render_template('login.html', body_class='bg login')

@boundary_bp.route('/login', methods=['POST'])
def login():
    role = request.form.get('role')
    username = request.form.get('username')
    password = request.form.get('password')
    user = AuthController.login(role, username, password)
    if user:
        session['user_id'] = user.id
        session['role'] = user.role
        session['username'] = user.username
        if user.role == 'User Admin':
            # land on CREATE USER as requested
            return redirect(url_for('boundary.admin_new_user'))
        if user.role == 'CSR Representative':
            return redirect(url_for('boundary.csr_dashboard'))
        if user.role == 'Person in Need':
            return redirect(url_for('boundary.pin_dashboard'))
        if user.role == 'Platform Manager':
            return redirect(url_for('boundary.pm_dashboard'))
    flash('Invalid credentials or suspended account.')
    return redirect(url_for('boundary.home'))

@boundary_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('boundary.home'))

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
    return render_template('user_admin.html', view='create', body_class='bg create')

@boundary_bp.route('/admin/users/create', methods=['POST'])
def admin_create_user():
    AuthController.require_role('User Admin')
    ok, msg = UserAdminController.create_user_with_profile(
        role=request.form.get('role'),
        username=request.form.get('username'),
        password=request.form.get('password'),
        active=True,
        full_name=request.form.get('full_name'),
        email=request.form.get('email'),
        phone=request.form.get('phone'),
    )
    flash(msg)
    return redirect(url_for('boundary.admin_users', type='profiles'))

@boundary_bp.route('/admin/users/<int:user_id>/edit', methods=['GET'])
def admin_edit_user(user_id):
    AuthController.require_role('User Admin')
    from ..entity.models import User
    user = User.query.get(user_id)
    if not user:
        flash('User not found.')
        return redirect(url_for('boundary.admin_users'))
    return render_template('user_admin.html', view='edit', user=user, body_class='bg create')

@boundary_bp.route('/admin/users/<int:user_id>/update', methods=['POST'])
def admin_update_user(user_id):
    AuthController.require_role('User Admin')
    ok, msg = UserAdminController.update_user_with_profile(
        user_id=user_id,
        role=request.form.get('role'),
        username=request.form.get('username'),
        password=request.form.get('password'),
        # this is here to fix the suspension of account when updating a user.
        active=request.form.get('active'),
        full_name=request.form.get('full_name'),
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
    history_items = CSRController.history() or []
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
    reqs = PINController.list_my_requests(q)
    return render_template('pin.html', view='dashboard', categories=categories, reqs=reqs, q=q)


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
    ok, msg = PINController.update_request(
        req_id,
        title=request.form.get('title'),
        description=request.form.get('description'),
        category_id=request.form.get('category_id'),
        status=request.form.get('status') or 'open'
    )
    flash(msg)
    return redirect(url_for('boundary.pin_dashboard'))


@boundary_bp.route('/pin/request/<int:req_id>/edit', methods=['GET'])
def pin_edit_req(req_id):
    AuthController.require_role('Person in Need')
    r = PINController.get_request(req_id)
    if not r:
        flash('Request not found or permission denied.')
        return redirect(url_for('boundary.pin_dashboard'))
    categories = PINController.get_categories()
    return render_template('pin.html', view='edit', req=r, categories=categories)


@boundary_bp.route('/pin/request/<int:req_id>/delete', methods=['POST'])
def pin_delete_req(req_id):
    AuthController.require_role('Person in Need')
    ok = PINController.delete_request(req_id)
    if ok:
        flash('Request deleted.')
    else:
        flash('Request not found or permission denied.')
    return redirect(url_for('boundary.pin_dashboard'))


@boundary_bp.route('/pin/history')
def pin_history():
    AuthController.require_role('Person in Need')
    categories = PINController.get_categories()
    category_id = request.args.get('category_id', type=int)
    start = request.args.get('start')
    end = request.args.get('end')
    items = PINController.history(category_id=category_id, start=start, end=end)
    return render_template('pin.html', view='history', categories=categories, items=items)

# ---------- Platform Manager ----------
@boundary_bp.route('/pm')
def pm_dashboard():
    AuthController.require_role('Platform Manager')
    categories = PMController.search_categories(request.args.get('q','').strip())
    return render_template('pm.html', view='dashboard', categories=categories, q=request.args.get('q','').strip())

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
    data = ReportController.generate(scope)
    return render_template('pm.html', view='reports', scope=scope, data=data)
