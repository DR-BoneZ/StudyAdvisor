from flask import Flask, request, Response
import json, sys, datetime, mysql.connector
from urlparse import urlparse
import connections

app = Flask(__name__)

@app.route("/.json", methods=["POST"])
def main():
	user_id = 0
	try:
		conn = mysql.connector.connect(host='localhost', database='study', user='root', password='password')
		cur = conn.cursor(buffered=True)
		if not (conn.is_connected()):
			print('Could not connect to MySQL database')
			exit()
		device_name = request.form['device']
		cur.execute("INSERT INTO users (device_name) SELECT %s FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM users WHERE device_name=%s);", (device_name, device_name))
		conn.commit()
		cur.execute("SELECT id FROM users WHERE device_name=%s LIMIT 1;", (device_name,))
		user_id_row = cur.fetchone()
		if(user_id_row is None): return "User not found"
		user_id = user_id_row[0]
		date = datetime.datetime.now()
		url = request.form['url']
		#if 'referer' in request.form:
		#	referer = request.form['referer']
		#else:
		referer = None
		parsed_uri = urlparse(url)
		domain = ('{uri.netloc}'.format(uri=parsed_uri)).replace('www.', '')
		cur.execute("SELECT * FROM `ignore` WHERE domain=%s LIMIT 1;", (domain,));
		if (len(cur.fetchall()) == 0):
			cur.execute("SELECT id FROM sites WHERE url=%s LIMIT 1;", (url,))
			site_id_row = cur.fetchone()
			if(site_id_row is None):
				cur.execute("INSERT INTO sites (url, visits) VALUES (%s, %s);", (url, 0))
				conn.commit()
				cur.execute("SELECT id FROM sites WHERE url=%s LIMIT 1;", (url,))
				site_id_row = cur.fetchone()
			site_id = site_id_row[0]
			if referer == None:
				cur.execute("SELECT site_id, date FROM users_join WHERE user_id='" + str(user_id) + "' ORDER BY date DESC;")
				from_id_row = cur.fetchone()
			else:
				cur.execute("SELECT id FROM  sites WHERE url=%s LIMIT 1;", (referer,))
				from_id_row = cur.fetchone()
                        if(from_id_row is None):
				cur.execute("INSERT INTO sites (url, visits) VALUES (%s, %s);", (url, 0))
				conn.commit()
				cur.execute("SELECT id FROM sites WHERE url=%s LIMIT 1;", (url,))
				from_id_row = cur.fetchone()
			from_id = from_id_row[0]
			if (site_id != from_id):
				cur.execute("INSERT INTO users_join (user_id, site_id, from_id, date) VALUES (%s, %s, %s, %s)", (user_id, site_id, from_id, date))
			if from_id is not None:
				cur.execute("UPDATE sites SET visits=visits+1 WHERE id=%s OR id=%s", (site_id, from_id))
				conn.commit()
				cur.execute("SELECT id FROM connections WHERE (site_id=%s AND from_id=%s) OR (site_id=%s AND from_id=%s) LIMIT 1;", (site_id, from_id, from_id, site_id))
				connect = cur.fetchone()
				if connect is None:
					cur.execute("INSERT INTO connections (site_id, from_id, connections) VALUES (%s, %s, 1);", (site_id, from_id))
					conn.commit()		
				else:
					cur.execute("UPDATE connections c SET c.connections=c.connections+1 WHERE id=%s", (connect[0],))
					conn.commit()		
	except mysql.connector.Error as e:
		ret = Response(str(e))
		ret.headers['Access-Control-Allow-Origin'] = '*'
		return ret
	else:
		conn.close()
		ret = Response(json.dumps(connections.get_suggestions(user_id, 10)))
		ret.headers['Access-Control-Allow-Origin'] = '*'
		return ret
	

if __name__ == '__main__':
	app.run(debug=True, host="0.0.0.0")
