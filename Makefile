
run_real_time_twillio:
	##@ngrok http 6060
	python src/realtime_twillio/main.py --call=+5511945348314

run_realtime:
	cd realtime \
	&& python push_to_talk_app.py

refresh_db:
	rm ./db/mock_sqlite.db \
	&& sqlite3 ./db/mock_sqlite.db < ./db/mock_patients_data.sql

unlock_db:
	chmod 777 ./db/mock_sqlite.db


app:
	streamlit run server/home.py

api:
	python realtime/call.py

