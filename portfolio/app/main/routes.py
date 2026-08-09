from app import db, mail
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, \
                           MessageForm, DeleteProfileForm
from app.models import User, Post, Notification, Message
from app.translate import translate
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
                  jsonify, current_app, session
from flask_babel import get_locale, _, gettext
from flask_login import current_user, login_required, logout_user
from langdetect import detect, LangDetectException
#from app.email import send_password_reset_email


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


# @bp.route est un décorateur, le user invoque l'url ci-dessous
# Flask retourne une réponse (notamment le 'return'..)
@bp.route('/')
def home():
    return redirect(url_for('about_me.about_me'))


@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user, 
                    language=language)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], 
        error_out=False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None

    # Jinja2 s'occupe de substituer les placeholders en arguments 
    # lors du rendement
    return render_template('index.html', title='Home Page', form=form, 
                           posts=posts.items, next_url=next_url, 
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], 
        error_out=False)
    next_url = url_for('main.user', username=user.username, 
                       page=posts.next_num) \
               if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, 
                       page=posts.prev_num) \
               if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items, 
                           form=form, next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)
    
    
@bp.route('/delete_profile', methods=['GET', 'POST'])
@login_required
def delete_profile():
    form = DeleteProfileForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        if user.check_password(form.password.data):
            db.session.delete(user)
            db.session.commit()
            flash('Your account has been deleted', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Wrong password', 'error')
        
        
    return render_template('delete_profile.html', title='Edit Profile',
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot follow yourself !')
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {} !'.format(username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods = ['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash('You cannot unfollow yourself !')
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('main.user', username=username))
    # Si jeton CSRF est manquante ou invalide on redirige à la page d'accueil
    else:
        return redirect(url_for('main.index'))


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], 
        error_out=False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Explore', 
                           posts=posts.items, next_url=next_url, 
                           prev_url=prev_url)


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    #print(type(posts))
    #print(total)
    #print(posts.all())
    #for post in posts:
    #   print(post.id)
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
               if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
               if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)


# Nous avons utilisé des request.form ici car il n'y a pas nécessairement
# de 'formulaire web' en tant que tel, alors qu'on utilise d'habitude
# le formulaire géré par Flask-WTF 
@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],
                                      request.form['source_language'],
                                      request.form['dest_language'])})


@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)


@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, 
                      body=form.message.data)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.add(msg)
        db.session.commit()
        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'],
            error_out=False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])
    


@bp.route('/language=<language>')
def set_language(language=None):
    session['language'] = language
    return redirect(request.referrer)


@bp.app_context_processor
def inject_conf_var():
    return dict(AVAILABLE_LANGUAGES=current_app.config['LANGUAGES'], 
                CURRENT_LANGUAGE=session.get('language', 
                                             request.accept_languages
                                             .best_match(current_app
                                                        .config['LANGUAGES']
                                                        .keys())))
