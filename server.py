from flask import Flask, redirect, render_template, request
from wiki_linkify import wiki_linkify
import markdown
import pg
import time

app = Flask('MyApp')

db = pg.DB(dbname='wiki_db')

@app.route('/')
def render_homepage():
    return render_template(
        'homepage.html',
        title='Homepage'
    )

@app.route('/<page_name>')
def render_placeholder(page_name):
    query = db.query("select pages.id, pages.pagename, content.content, content.timestamp from pages,content where content.pageid = pages.id and pages.pagename = '%s' order by content.timestamp desc limit 1" % page_name)
    results = query.namedresult()
    # print "Query: %r" % query
    is_available = False
    # print "Length: %d" % len(query.namedresult())
    if len(results) < 1:
        is_available = True
        db.insert(
            'pages', {
                'pagename': page_name
            }
        )
        newid = db.query("select * from pages where pages.pagename = '%s'" %page_name).namedresult()[0].id
        db.insert(
            'content', {
                'pageid': newid,
                'content': "",
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            }
        )

        wiki_page = db.query("select pages.id, pages.pagename, content.pageid, content.content, content.timestamp from pages, content where pages.id = content.pageid and pages.pagename = '%s'" % page_name).namedresult()[0]
    else:
        wiki_page = results[0]
    # if page_name in db.('wiki',)
    # db.insert('wiki', pagename=page_name,content="")
    content = markdown.markdown(wiki_linkify(wiki_page.content))
    return render_template(
        'placeholder.html',
        page_name = page_name,
        is_available = is_available,
        wiki_linkify = wiki_linkify,
        content = content,
        markdown = markdown,
        wiki_page = wiki_page
    )

@app.route('/<page_name>/edit')
def render_pageEdit(page_name):
    # query = db.query("select * from pages where pagename = '%s'" % page_name)
    query = db.query("select pages.id, pages.pagename, content.content as content_info, content.timestamp from pages,content where content.pageid = pages.id and pages.pagename = '%s' order by content.timestamp desc limit 1" % page_name)
    wiki_page = query.namedresult()[0]
    content = wiki_page.content_info
    print "CONTENT: %r" % content
    return render_template(
        'page_edit.html',
        page_name = page_name,
        content = content,
        wiki_linkify = wiki_linkify,
        markdown = markdown,
        wiki_page = wiki_page
    )

@app.route('/<page_name>/hist')
def showHist(page_name):
    query = db.query("select pages.id, pages.pagename, content.content, content.timestamp, content.id as content_id from pages,content where content.pageid = pages.id and pages.pagename = '%s' order by content.timestamp" % page_name)
    return render_template(
    'pagehist.html',
    hist = query.namedresult()
    )

@app.route('/<page_name>/hist/record')
def renderHist(page_name):
    id = request.args.get('id')
    result = db.query("select pages.pagename, content.content, content.timestamp from pages,content where pages.id = content.pageid and content.id = '%s'" % id).namedresult()[0]

    content = markdown.markdown(wiki_linkify(result.content))
    return render_template(
    'one_hist_record.html',
    name = result.pagename,
    content = content,
    )

@app.route('/<page_name>/save', methods=['POST'])
def saveEdit(page_name):
    page_id = request.form.get('id')
    print "PAGE NAME: %r" % page_name
    content=request.form.get('content')
    db.insert(
        'content', {
            'pageid': page_id,
            'content': content,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
    )

    return redirect('/%s' % page_name)

@app.route('/allpages')
def allPages():
    query = db.query('select * from wiki')
    return render_template(
        'allpages.html',
        results = query.namedresult()
    )

@app.route('/search', methods=['POST'])
def redirect_search():
    search_val = request.form.get('search')
    return redirect('/%s' % search_val)

@app.route('/')
def camel(word):
    return wiki_linkify(word)

if __name__ == '__main__':
    app.run(debug=True)
