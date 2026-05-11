from flask import Flask,render_template,request,redirect
from model import db,studentsform
from flask_migrate import Migrate

app=Flask( __name__)
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://root:Boobalan%40333@localhost/dummy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db.init_app(app)
migrate=Migrate(app,db)

@app.route('/',methods=['GET','POST'])

def index():
    if request.method=='POST':
        Name=request.form['name']  
        
        issue_date=request.form['issue_date'] 
        Return_date=request.form['return_date']
       
        Mail_id=request.form['email']
        book_id=request.form['book_id']
        Department=request.form['department'] 
        College=request.form['college']
        form=studentsform(Name=Name,issue_date=issue_date,return_date=Return_date,Mail_id=Mail_id, book_id=book_id,Department=Department,college=College)
        db.session.add(form)
        db.session.commit()
        
        

      

    return render_template('index.html')
@app.route('/details',methods=['GET','POST'])
def details():
       
   return render_template('form.html')
  

@app.route("/display",methods=['GET','POST'])
def display():
    studentform=studentsform.query.all()
    return render_template("display.html",forms=studentform)
@app.route('/update/<int:id>',methods=['GET','POST'])
def update(id):
    data=studentsform.query.get(id)


    if request.method=="POST" :
    
       data.Name=request.form['name']
       data.issue_date=request.form['issue_date']
       data.return_date=request.form['return_date']
       data.Mail_id=request.form['email']
       data.book_id=request.form['book_id']
       data.Department=request.form['department']
       data.College=request.form['college']
     
       db.session.commit()
       return redirect("/display")

    return render_template('update.html',data=data)


@app.route("/delete/<int:id>")
def delete(id):
    data=studentsform.query.get(id)
    if data:
      db.session.delete(data)
      db.session.commit()

    return redirect("/display")
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/contact")
def contact():
    return render_template("contact.html")


if __name__ == '__main__':
    app.run(debug=True)