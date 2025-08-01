from datetime import datetime, timezone

import sqlalchemy as sa

from flask import render_template, flash, redirect, url_for
from flask_login import login_user, current_user, logout_user, login_required
from flask import request
from urllib.parse import urlsplit


from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, \
    EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm, \
    CommentForm
from app.models import User, Post, Comment
from app.utils import send_password_reset_email

from config import Config


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    # posts = db.session.scalars(current_user.following_posts()).all()
    posts = db.paginate(current_user.following_posts(),
                        page=page, per_page=Config.POSTS_PER_PAGE,
                        error_out=False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home',
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url, form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data)
        )
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    profile = db.first_or_404(sa.select(User).where(User.username==username))
    page = request.args.get('page', 1, type=int)
    query = profile.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page, per_page=Config.POSTS_PER_PAGE,error_out=False)
    post_count = posts.total
    next_url = url_for('user', username=profile.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=profile.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=profile, posts=posts.items, form=form, next_url=next_url, prev_url=prev_url, post_count=post_count)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form=EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)


@app.route('/edit_post/<post_id>', methods=['GET', "POST"])
@login_required
def edit_post(post_id):
    form = PostForm()
    post = db.session.scalar(sa.select(Post).where(Post.id == post_id))
    if form.validate_on_submit():
        if post is None:
            flash("Post is expired!")
            return redirect(url_for('index'))
        if post.author != current_user:
            flash("You are not authorized!")
            return redirect(url_for('index'))
        post.body = form.post.data
        db.session.commit()
        flash("Updated post")
        return redirect(url_for('post_details', post_id=post.id))
    if request.method == 'GET':
        form.post.data = post.body
    return render_template('edit_post.html', title='Edit Post', form=form)


@app.route('/post_details/<post_id>', methods=['GET', 'POST'])
@login_required
def post_details(post_id):
    # form = PostForm()
    post = db.session.scalar(sa.select(Post).where(Post.id == post_id))
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        post_id = int(request.form['comment_post_id'])
        comment = Comment(body=comment_form.body.data, author=current_user, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
        flash("Comment added")
        return redirect(url_for('post_details',post_id=post.id ))
    return render_template('post_detail.html', title='Post Details', post=post, comment_form=comment_form)


@app.route('/follow/<username>',methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username)
        )
        if user is None:
            flash(f"User {username} not found.")
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f"You are following {username}!")
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>',methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username)
        )
        if user is None:
            flash(f"User {username} not found.")
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f"You have unfollowed {username}.")
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    # posts = db.session.scalars(query).all()
    posts = db.paginate(query, page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html',
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data)
        )
        if user:
            send_password_reset_email(user)
        flash("Check your email for the instructions to reset your password")
        return redirect(url_for('login'))
    return render_template('email/reset_password.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('email/reset.html', form=form)