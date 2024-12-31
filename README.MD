Dự án này với mục đích xây dựng một luồng dữ liệu real-time về thời tiết.

Data pipeline  API: OpenWeatherMap --> kafka producer --> topic-raw --> processed by spark streaming --> topic-processed -->  kafka consumer --> mongo db --> power BI.