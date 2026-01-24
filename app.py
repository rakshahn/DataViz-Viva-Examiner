from flask import Flask,render_template,request,redirect,url_for

app=Flask(__name__)

@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        username=request.form.get("username")
        return redirect(url_for("chat",name=username))
    return render_template("login.html")

@app.route("/chat")
def chat():
    name=request.args.get("name")
    return render_template("chat.html",name=name)

if __name__=="__main__":
    app.run(debug=True)