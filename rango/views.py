from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import login, authenticate, logout
from rango.models import Category, Page, UserProfile
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from datetime import datetime
from rango.bing_search import run_query
from django.contrib.auth.models import User

def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__startswith=starts_with)
    else:
        cat_list = Category.objects.all()

    if max_results > 0:
        if (len(cat_list) > max_results):
            cat_list = cat_list[:max_results]

    for cat in cat_list:
        cat.url = encode_url(cat.name)

    return cat_list

def decode_url(str):
    return str.replace('_', ' ')

def encode_url(str):
    return str.replace(' ', '_')

def index(request):
    ### testowanie ciasteczek, patrz register view
    #request.session.set_test_cookie()
    # ----> 1st version
    #return HttpResponse("Rango says hello world! <a href=\"/rango/about\">-- About --</a>")
    # <----

    # Request the context of the request.
    # The context contains information such as the client's machine details, for example.
    context = RequestContext(request)

    # Construct a dictionary to pass to the template engine as its context.
    # Note the key boldmessage is the same as {{ boldmessage }} in the template!
    #context_dict = {'boldmessage': "I am bold font from the context"}

    # Return a rendered response to send to the client.
    # We make use of the shortcut function to make our lives easier.
    # Note that the first parameter is the template we wish to use.

    # Query the database for a list of ALL categories currently stored.
    # Order the categories by no. likes in descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list in our context_dict dictionary which will be passed to the template engine.
    category_list_most_liked = Category.objects.order_by('-likes')[:5]
    category_list_most_viewed = Category.objects.order_by('-views')[:5]

    # The following two lines are new.
    # We loop through each category returned, and create a URL attribute.
    # This attribute stores an encoded URL (e.g. spaces replaced with underscores).
    for category in category_list_most_liked:
        category.url = category.name.replace(' ', '_') # albo encode(category.name)
    for category in category_list_most_viewed:
        category.url = category.name.replace(' ', '_') # albo encode(category.name)

    context_dict = {'categories_most_viewed' : category_list_most_viewed,
     'categories_most_liked' : category_list_most_liked }

    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list

    page_list = Page.objects.order_by('-views')[:5]
    context_dict['pages'] = page_list

    """
    ### NEW CODE ### COOKIES
    # Obtain our Response object early so we can add cookie information.
    response = render_to_response('rango/index.html', context_dict, context)

    # Get the number of visits to the site.
    # We use the COOKIES.get() function to obtain the visits cookie.
    # If the cookie exists, the value returned is casted to an integer.
    # If the cookie doesn't exist, we default to zero and cast that.
    visits = int(request.COOKIES.get('visits', 0))

    # Does the cookie last_visit exist?
    if request.COOKIES.has_key('last_visit'): # or if 'last_visit in request.COOKIES then'
        # Yes, it does! Get the cookie's value.
        last_visit = request.COOKIES['last_visit']
        # Cast the value to a Python date/time object.
        last_time_visit = datetime.strptime(last_visit[:-7], '%Y-%m-%d %H:%M:%S')

        # If it's been more than one day since last visit...
        if (datetime.now()-last_time_visit).seconds>5:
            # ...reassign the value of the cookie to +1 of what it was before...
            response.set_cookie('visits', visits+1)
            # ...and update the last visit cookie, too.
            response.set_cookie('last_visit', datetime.now())
    else:
            # Cookie last_visit doesn't exist, so create it to the current date/time.
            response.set_cookie('last_visit', datetime.now())
    ### End NEWCODE ###
    """

    ### NEW CODE ###
    if request.session.get('last_visit'):
        # The session has a value for the last visit
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        if(datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
            request.session['visits']+=1
            request.session['last_visit'] = str(datetime.now())
    else:
        # The get returns None, and the session does not have a value for the last visit.
        request.session['last_visit'] = str(datetime.now())
        request.session['visits']=1
    ### END NEW CODE ###

    # Render the response and return to the client, updating any cookies that need changed.
    response = render_to_response('rango/index.html', context_dict, context)
    return response

def about(request):
    ### ---> 1st version
    #return HttpResponse("Rango Says: Here is the about page. <a href=\"/rango\">-- Index --</a>")
    ### <---
    ### New code ### patrz index() sesje

    context=RequestContext(request)
    context_dict={}

    cat_list=get_category_list()
    context_dict['cat_list']=cat_list

    if request.session.get('visits'):   # or count = request.session.get('visits',0)
        count = request.session.get('visits')
    else:
        count=0
    ### End code ###

    context_dict['visits']=count
    return render_to_response('rango/about.html', context_dict, context)

def category(request, category_name_url):
    # Request our context from the request passed to us.
    context = RequestContext(request)

    # Change underscores in the category name to spaces.
    # URLs don't handle spaces well, so we encode them as underscores.
    # We can then simply replace the underscores with spaces again to get the name.
    category_name = category_name_url.replace('_', ' ') # or decode(category_name_url)

    # Create a context dictionary which we can pass to the template rendering engine.
    # We start by containing the name of the category passed by the user.
    context_dict = {'category_name' : category_name, 'category_name_url' : category_name_url}

    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list

    try:
        # Can we find a category with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(name__iexact=category_name)

        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
        pages = Page.objects.filter(category=category).order_by('-views')

        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        # Add category to the context so that we can access the id and likes
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass
        # could be
        # from django.http import Http404
        # raise Http404
        # or shortcut using 'get_object_or_404(Category, pk=name)'

    context_dict['submitted']=request.POST # zeby dac 'noresults found'
                                            # tylko wtedy gdy submitujemy
                                            # pusty form,
                                            # see category.html result_list
    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            query = query.strip()
            result_list=run_query(query)
            context_dict['result_list']=result_list



    # Go render the response and return it to the client.
    return render_to_response('rango/category.html', context_dict, context)

@login_required
def add_category(request):
    # Get the context from the request.
    context = RequestContext(request)
    context_dict={}
    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list

    # A HTTP POST ?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form ?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)

            # Now call the index() view.
            # The user will be shown the homepage.
            return index(request)
        else:
            # The supplied form contained errors - just print them th the terminal.
            print form.errors
    else:
        # If the requested method was not a POST, display the form to enter details.
        form = CategoryForm()
    context_dict['form'] = form

    # Bad form (of form details), no form supplied...
    # Render the form with error messages (if any).
    return render_to_response('rango/add_category.html', context_dict, context)

@login_required
def add_page(request, category_name_url):
    context = RequestContext(request)
    cat_list=get_category_list()

    category_name = decode_url(category_name_url)
    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            # This time we cannot commit straight away.
            # Not all fields are automatically populated!
            page = form.save(commit=False)

            # Retrieve the associated Category object so we can add it.
            # Wrap the code in a try block - check if the category actually exists!
            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                return render_to_response('rango/add_category.html', {}, context)

            # Also, create a default value for the number of views.
            page.views = 0

            # With this, we can then save our new model instance.
            page.save()

            # Now that the page is saved, display the category instead.
            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()

    return render_to_response('rango/add_page.html',
        { 'category_name_url' : category_name_url,
       'category_name' : category_name, 'form' : form, 'cat_list' : cat_list },
       context)

def register(request):
    ### testowanie ciastek, patrz index view
    #if request.session.test_cookie_worked():
        #print ">>> TEST COOKIE WORKED!"
        #request.session.delete_test_cookie()

    context=RequestContext(request)
    cat_list=get_category_list()

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UseForm and UserProfileForm.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid.
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide any profile picture ?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else ?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    # Render the template depending on the context.
    return render_to_response('rango/register.html',
    {'user_form' : user_form, 'profile_form' : profile_form,
    'registered' : registered, 'cat_list' : cat_list },
    context)

def user_login(request):
    context = RequestContext(request)
    cat_list=get_category_list()

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use the Django's machinery to attempt to see if the username/password combination is valid
        # - a User objectis returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of value), no user
        # with matching credentials was found.
        if user is not None:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                # An inactive account was used - no loggin in!
                return HttpResponse("Your Rango account is disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    # The request is not HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the blank dict object...
        return render_to_response('rango/login.html', {'cat_list' : cat_list},
        context)

@login_required
def restricted(request):
    context = RequestContext(request)
    cat_list=get_category_list()

    return render_to_response('rango/restricted.html', {'cat_list' : cat_list },
        context)

@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log him out.
    logout(request)

    # Take the user back to the homepage.
    return HttpResponseRedirect('/rango/')

def search(request):
    context = RequestContext(request)
    cat_list=get_category_list()
    result_list=[]

    if request.method=='POST':
        query=request.POST['query'].strip()

        if query:
            # Run our Bing func to get the results list!
            result_list = run_query(query)

    return render_to_response('rango/search.html', {'result_list':result_list,
        'cat_list' : cat_list }, context)

@login_required
def profile(request):
    context=RequestContext(request)
    cat_list=get_category_list()
    context_dict={'cat_list':cat_list}
    u = User.objects.get(username=request.user)

    try:
        up = UserProfile.objects.get(user=u)
    except:
        up = None

    context_dict['user'] = u
    context_dict['userprofile'] = up
    print u, up

    return render_to_response('rango/profile.html', context_dict, context)

def track_url(request):
    context=RequestContext(request)
    page_id=None
    url='/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views+1
                page.save()
                url=page.url
            except:
                pass
    return redirect(url)


@login_required
def like_category(request):
    context=RequestContext(request)
    cat_id=None
    if request.method == 'GET':
        cat_id=request.GET['category_id']
    likes=0
    if cat_id:
        category=Category.objects.get(id=int(cat_id))
        if category:
            likes=category.likes+1
            category.likes=likes
            category.save()

    return HttpResponse(likes)

def suggest_category(request):
    context=RequestContext(request)
    cat_list=[]
    starts_with=''
    if request.method == 'GET':
        starts_with = request.GET['suggestion']
    cat_list = get_category_list(8, starts_with)

    return render_to_response('rango/category_list.html', \
    {'cat_list' : cat_list }, context)


@login_required
def auto_add_page(request):
    context=RequestContext(request)
    cat_id=None
    url=None
    title=None
    context_dict={}
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        url = request.GET['url']
        title = request.GET['title']
        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            p = Page.objects.get_or_create(category=category, title=title, url=url)

            pages = Page.objects.filter(category=category).order_by('-views')

            # Adds our results list to the template context under name pages.
            context_dict['pages'] = pages
    return render_to_response('rango/page_list.html', context_dict, context)

