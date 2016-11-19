# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################
import datetime


def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simple replace the two lines below with:
    return auth.wiki()
    """
    response.flash = T("Hi, Have a Nice Day")
    return locals()


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())


@auth.requires_login()
def recentadditions():
    form=db().select(orderby=~db.books.created_on,limitby=(0,5))
    return locals()
    
def redirect_after_login(form):
	redirect(URL(r=request,f='index.html',args=[0]))
def redirect_after_register(form):
    redirect(URL(r=request,f='index.html',args=[0]))

auth.settings.login_onaccept.append(redirect_after_login)
auth.settings.register_onaccept.append(redirect_after_register)
#auth.settings.table_user.password.requires = IS_STRONG(min=8,special=1,upper=1,lower=1)
@auth.requires_login()
def my_profile():
    a = db(db.auth_user.id ==  auth.user_id).select(db.auth_user.ALL)
    return locals()

@auth.requires_login
def show_user():
    id2 = request.args(0)
    a = db(db.auth_user.id ==  id2).select(db.auth_user.ALL)
    id1 = auth.user_id
    return locals()

@auth.requires_login()
def show_users():
    id1 = auth.user_id
    a = db(db.auth_user.id != auth.user_id).select(db.auth_user.ALL)
    return locals()
#-----------------------------------------posts------------------------------------------------------#
import re
import os

@auth.requires_membership('managers')
def admin():
    return locals();

@auth.requires_membership('managers')
def updatebooks():
    form=SQLFORM(db.books).process()
    if form.accepted :
        redirect(URL('index.html'))
    else:
        response.flash=('Fill the form correctly')
    return locals()

@auth.requires_membership('managers')
def updatejournals():
    form=SQLFORM(db.journals).process()
    if form.accepted :
        redirect(URL('index'))
    else:
        response.flash=('Fill it correctly')
    return locals()

@auth.requires_membership('managers')
def updatethesis():
    form=SQLFORM(db.thesis).process()
    if form.accepted :
        redirect(URL('index.html'))
    else:
        response.flash=('Fill the form correctly')
    return locals()

@auth.requires_membership('managers')
def updateejournals():
    form=SQLFORM(db.e_journals).process()
    if form.accepted :
        redirect(URL('index.html'))
    else:
        response.flash=("Fill it correctly")
    return locals()

def showejournals():
    ejournals=db(db.e_journals).select(orderby=db.e_journals.title)
    return locals()

def showjournals():
    journals=db(db.journals).select(orderby=db.journals.title)
    return locals()

def showbooks():
    books=db(db.books).select(orderby=db.books.title)
    return locals()

def showebooks():
    ebooks=db(db.e_book).select(orderby=db.e_book.Title)
    return locals()

def showthesis():
    thesis=db(db.thesis).select(orderby=db.thesis.title)
    return locals()

@auth.requires_membership('managers')
def issue_book():
    time=datetime.date.today()
    b=time+datetime.timedelta(days=15)
    form=SQLFORM(db.issue_books).process()
    db.issue_books.return_date.default=b
    if form.accepted :
        redirect(URL('index.html'))
    else:
        response.flash=('Fill it correctly')
    return locals()

def extra():
    return locals();

@auth.requires_login()  
def fine_calculator():
    ref_no=request.args(0,cast=int) or 0
    if ref_no==0:
        session.flash="Cannot Access"
        redirect(URL('index.html'))
    book=db(db.issue_books.ref_no==ref_no).select(db.issue_books.ALL)[0]
    books=db(db.books.ref_no==ref_no).select(db.books.ALL)[0]
    return_date=book.return_date
    time=datetime.date.today()
    if return_date-time<0:
        fine=5*abs(return_date-time)
    else:
        fine=0
    return locals()

@auth.requires_membership('managers')
def return_book():
    time=datetime.date.today()
    form= SQLFORM.factory(Field('ref_no'))
    if form.process().accepted:
        d=db(db.issue_books.ref_no==form.ref_no).select()
        if d:
	        db(db.issue_books.id==d.id).delete()
	        redirect(URL('fine_calculator.html',args=(d.return_date)))
        else:
	        response.flash=("No Book with given ref_no. is issued")
    return locals()

@auth.requires_membership('managers')
def purchase_book():
    form=SQLFORM.factory(Field('ref_no','string',required=True)).process()
    if form.process().accepted:
        if db(db.books.ref_no==form.ref_no).select() and not db(db.issue_books.ref_no==form.ref_no).select(db.books):
            db(db.books.ref_no==form.ref_no).delete()
            redirect(URL('index.html'))
        else:
            response.flash="This book is not present"
    return locals()

@auth.requires_login()   
def askyourqueries():
    form=SQLFORM(db.ask).process()
    if form.process().accepted:
        redirect(URL('index.html'))
    else:
        response.flash=("Fill Your Queries Correctly")
    return locals()

@auth.requires_membership('managers')
def uploadebooks():
    form=SQLFORM(db.e_book).process()
    if form.process().accepted:
        session.flash="Your E-BOOK is under authetication"
        redirect(URL("index.html"))
    else :
        response.flash=("Upload the Book Properly")
    return locals()

@auth.requires_membership('managers')
def view_recommendation():
    s=db().select(db.recommend.ALL)
    return locals()

@auth.requires_login() 
def recommend():
    form=SQLFORM(db.recommend).process() 
    if(form.process().accepted):
        session.flash("Your Recommendation is under Consideration")
        redirect(URL('index.html'))
    else:
        response.flash=('Please Recommend the book properly')  
    return locals()

@auth.requires_membership('managers')
def lost_book():
    now=datetime.date.today()
    form=SQLFORM(db.lost_book)
    if form.process().accepted:
    #  new=db(db.books.ref_no==form.book_ref).select()
    # fine=new[0].cost
        db(db.books.ref_no==form.vars.book_ref).delete()
        session.flash=("Form Submitted")
        redirect(URL('index.html'))
    else:
        session.flash="Fill it Carefully"
    return locals()

@auth.requires_membership('managers')
def answerqueries():
    post=db.ask(request.args(0,cast=int))
    db.answer_query.postid.default=post.id
    db.answer_query.postid.readable=db.answer_query.postid.writable=False
    form=SQLFORM(db.answer_query).process()
    if form.process().accepted:
        redirect(URL('index.html'))
    else:
        response.flash=("fill it correctly")
    return locals()

@auth.requires_membership('managers')
def newnews():
    form=SQLFORM(db.news).process()
    if (form.process().accepted):
        redirect(URL('index.html'))
    else:
        response.flash=('Fill the new Properly')
    return locals()

@auth.requires_membership('managers')
def editnews():
    news=request.args(0,cast=int)
    if news:
        new=db(db.news.id==news).select(db.news.ALL)
        post=SQLFORM(db.news,news,deletable=True,fields=['Title','cont'])
        if post.process().accepted:
            new.cont=post.vars.cont
            new.Title=post.vars.Title
            new.update_record()
            session.flash="successfully updated"
        elif post.errors:
            response.flash='Errors in form'
    return locals()

@auth.requires_membership('managers')
def deletenews():
    pid=request.args(0)
    if pid:
        db(db.news.id==pid[0]).delete()
        session.flash='Deleted'
    else:
        session.flash="Invalid"
    redirect(URL('index.html'))
    return locals()

def testing():
    mail.send(to=['sksshashank901@gmail.com'],
            subject="nots",
            message="aszxc"
            )
    redirect('http://www.google.com')
    return locals()
    
@auth.requires_membership('managers')
def overdue():
    now=datetime.date.today()
    li=[]
    emails=" asdfafd "
    datab=db(db.issue_books.return_date < now).select(db.issue_books.ALL)
    for i in datab:
        news=db(db.auth_user.roll_no==i.identity_number).select(db.auth_user.ALL)
        li.append(news[0].first_name)
        li.append(news[0].email)
        li.append((str)(i.ref_no))
        mess="Dear "+li[0]+",\nBook with Ref. No. "+li[2]+"which was issued to you is overdue";
        mail.send(to=li[1],
          subject= 'BOOK OVERDUE NOTICE',
           message=mess)
        li=[]
    session.flash="successfully sent mail"
    redirect('index')
    return locals()

def shownews():
    row=db(db.news.id > 0).select(db.news.ALL)
    return locals()

@auth.requires_membership('managers')
def addcontacts():
    form=SQLFORM(db.contacts)
    if form.process().accepted:
        session.flash=("New Contact have been added")
        redirect(URL('index.html'))
    else:
        session.flash=("Fill it correctly")
    return locals()

@auth.requires_membership('managers')
def managecontacts():
    grid=SQLFORM.grid(db.contacts)
    return locals()

@auth.requires_login()
def feed():
    form=SQLFORM(db.feedback)
    if form.process().accepted:
        session.flash="Your feedback have been submitted"
        redirect(URL('index.html'))
    else:
        session.flash="Fill the Feedback Properly"
    return locals()

def viewfeedbacks():
    new=db(db.feedback.id>0).select(orderby=~db.feedback.created_on)
    return locals()

@auth.requires_membership('managers')
def deletefeedback():
    r=request.vars.pid
    if r:
        db(db.feedback.id==r).delete()
        session.flash=("Feedback Deleted!")
        redirect(URL('viewfeedback.html'))
    else:
        session.flash=("Provide Valid feedback")
        redirect(URL('viewfeedback.html'))
    return locals()

def searchbooks():
    return dict(form=FORM(INPUT(_id='keyword',_name='keyword',_onkeyup="ajax('callback',['keyword'],'target');")), target_div=DIV(_id='target',_class='hehe'))

def callback():
    query=db.books.title.contains(request.vars.keyword)
    pages=db(query).select(orderby=db.books.title)
    links=[]
    links=[A(p.title,_href=URL('show',args=p.id)) for p in pages]
    if links:
        return OL(*links)
    links.append("No matching result found")
    return links

def show():
    p=request.args(0)
    if p:
        p=int(p)
        show=db(db.books.id==p).select(db.books.ALL)[0]
    return locals()

def searchjournals():
    return dict(form=FORM(INPUT(_id='keyword',_name='keyword',_onkeyup="ajax('callback1',['keyword'],'target');")), target_div=DIV(_id='target',_class='hehe'))

def callback1():
    query=db.journals.title.contains(request.vars.keyword)
    pages=db(query).select(orderby=db.journals.title)
    links=[]
    links=[A(p.title,_href=URL('showsearchedjournals',args=p.id)) for p in pages]
    if links:
        return OL(*links)
    links.append("No matching result found")
    return links

def faq():
    return locals();

def feedback():
    return locals();

def hours():
    return locals();

def contacts():
    select=db(db.contacts.id > 0).select(db.contacts.ALL)
    return locals();

def rules():
    return locals();

def services():
    return locals();

def showsearchedjournals():
    p=request.args(0)
    if p:
        p=int(p)
        show=db(db.journals.id==p).select(db.journals.ALL)[0]
    else:
        show="Cannot Directly access"
    return locals()
