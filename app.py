# Importing Reqired Module.
import os 
from flask import *
import sqlite3
import difflib
import openai as ai             # Detail Library.
from tmdbv3api import TMDb, Movie
from dotenv import load_dotenv

# Recommendation Library.
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
#########################




# Intial Setup.
app= Flask(__name__)
app.secret_key="123"
load_dotenv()
OPENAI_API_KEY=os.getenv('API_KEY1')
TMDB_API=os.getenv('API_KEY2')

con=sqlite3.connect("database.db")
con.execute("create table if not exists customer(pid integer primary key,name text,address text,contact text,mail text)")
con.close()

# Preparing Model for further use.
df2 = pd.read_csv("./static/model/tmdb.csv" ,engine="python")
pd.set_option('display.max_colwidth', None)

count = CountVectorizer(stop_words='english')
count_matrix = count.fit_transform(df2['soup'])

cosine_sim2 = cosine_similarity(count_matrix, count_matrix)

df2 = df2.reset_index()
indices = pd.Series(df2.index, index=df2["title"])
all_titles = [df2["title"][i] for i in range(len(df2["title"]))]
###########################




# Home Page.
@app.route("/")
def index():
    return render_template("index.html", type1="inline-flex", type2="none", title="Advorrst")
###########################




# Login-Register Functionality.
@app.route('/login',methods=["GET","POST"])
def login():
    if request.method=='POST':
        name=request.form['name'].strip()
        password=request.form['password'].strip()
        con=sqlite3.connect("database.db")
        con.row_factory=sqlite3.Row
        cur=con.cursor()
        cur.execute("select * from customer where name=? and mail=?",(name,password))
        data=cur.fetchone()

        if data:
            session["name"]=data["name"]
            session["mail"]=data["mail"]
            return redirect("app")
        else:
            flash("Username and Password Mismatch","danger")
    return redirect(url_for("index"))    


@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        try:
            name=request.form['name'].strip()
            address=request.form['address'].strip()
            contact=request.form['contact'].strip()
            mail=request.form['mail'].strip()
            con=sqlite3.connect("database.db")
            cur=con.cursor()
            cur.execute("insert into customer(name,address,contact,mail)values(?,?,?,?)",(name,address,contact,mail))
            con.commit()
            flash("Record Added  Successfully","success")
        except:
            flash("Error in Insert Operation","danger")
        finally:
            return redirect(url_for("index"))
            con.close()

    return render_template('register.html', type1="inline-flex", type2="none", title="Register")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("index"))        
####################################################################################




# App Page.
@app.route("/app")
def test():
    return render_template("app.html", type1="none", type2="inline-flex", title="App")
###########################

  


# Recommendation Functionality.
def get_recommendations(title):
    cosine_sim = cosine_similarity(count_matrix, count_matrix)
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:11]
    movie_indices = [i[0] for i in sim_scores]
    id = df2['id'].iloc[movie_indices]
    tit = df2["title"].iloc[movie_indices]
    dat = df2['release_date'].iloc[movie_indices]
    vote = df2['vote_average'].iloc[movie_indices]
    
    return_df = pd.DataFrame(columns=["title", 'Year', 'Id', 'Vote'])
    return_df["title"] = tit
    return_df['Year'] = dat
    return_df['Id'] = id   
    return_df['Vote'] = vote 

    return return_df


# Recommendation ready. Now have to pass data to detail page.
@app.route('/app/search', methods=['POST'])
def searchmoiv():
    m_name = difflib.get_close_matches(request.form["movie_name"].strip(),all_titles,n=1)

    if len(m_name)==0:
        return render_template("notfound.html", type1="none", type2="inline-flex", title="4O4: MovieNotFound")
    else:
        m_name=str(m_name[0])

        result_final = get_recommendations(m_name)
        names = []
        dates = []
        ids= []
        vote=[]
        for i in range(len(result_final)):
            names.append(result_final.iloc[i][0])
            dates.append(result_final.iloc[i][1])
            ids.append(result_final.iloc[i][2])
            vote.append(result_final.iloc[i][3])
        return render_template('search.html', length=len(names), movie_names=names, movie_date=dates, like=vote, id=ids, search_name=m_name , type1="none", type2="inline-flex", title="Search")
####################################################################################




# Details Page Functionality.
def create_data(mname):
    metadata=[]
    tmdb=TMDb()
    tmdb.api_key = TMDB_API
    mov = Movie()
    
    dmid= df2[df2['title']==mname]['id'].to_string(index=False)
    apimovdet = mov.details(dmid)

    dmtag= df2[df2['id']==int(dmid)]['tagline'].to_string(index=False)
    about= df2[df2['id']==int(dmid)]['overview'].to_string(index=False)
    dmgenre= df2[df2['id']==int(dmid)]['genres'].to_string(index=False).strip("[]").split(',')
    vote= df2[df2['id']==int(dmid)]['vote_average'].to_string(index=False)
    run= df2[df2['id']==int(dmid)]['runtime'].to_string(index=False)
    date= df2[df2['id']==int(dmid)]['release_date'].to_string(index=False)
    cast= df2[df2['id']==int(dmid)]['cast'].to_string(index=False).strip("[]").split(',')
    direct= df2[df2['id']==int(dmid)]['director'].to_string(index=False)

    metadata.append(dmtag)
    metadata.append(about)
    metadata.append(dmgenre)
    metadata.append(vote)
    metadata.append(run)
    metadata.append(date)
    metadata.append(cast)
    metadata.append(direct)
    metadata.append(apimovdet.backdrop_path)
    metadata.append(apimovdet.trailers['youtube'][0]['source'])

    return metadata


# Details ready. Now have to pass data to detail page.
@app.route("/app/search/details/<name>", methods=["POST"])
def detail(name):
    metdat= create_data(name)
    try:
        ai.api_key=  OPENAI_API_KEY

        msg= [
            {
                'role': 'system',
                'content': "You're kind and helpful assistent."
            },
        ]

        ask= name+" movie overview in short."

        msg.append( {'role': 'user', 'content': ask}, )

        chat= ai.ChatCompletion.create(model= 'gpt-3.5-turbo', messages= msg)

        reply= chat.choices[0].message.content

    except:
        reply= metdat[1]    

    finally:
        return render_template("detail.html", metadata= metdat, about=reply, type1="none", type2="inline-flex", title=name)  
####################################################################################




# About Page.
@app.route("/app/about")
def about():
    return render_template("about.html", type1="inline-flex", type2="none", title="About Us")
###########################




# App Exection.
if __name__== "__main__":
    app.run(debug=False, host='0.0.0.0')
