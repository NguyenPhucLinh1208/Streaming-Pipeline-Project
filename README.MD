# I. Overview

Dự án này với mục đích xây dựng một luồng dữ liệu real-time về thời tiết.

Data pipeline  API: OpenWeatherMap --> kafka producer --> topic-raw --> processed by spark streaming --> topic-processed -->  kafka consumer --> mongo db --> power BI.

# II. API openweathermap.

## 1. Thu thập coordinates.

* Thành phố Hà Nội: 30 đơn vị hành chính cấp huyện, gồm 17 huyện, 12 quận, 1 thị xã
* Thành hố Hồ Chí Minh: Hồ Chí Minh bao gồm 24 quận huyện
* Như vậy, có 54 điểm, lưu vào file cố định 

## 2. Thu thập dữ liệu hiện tại:

* Thời tiết hiện tại
* Ô nhiễm không khí hiện tại

## 3. Thu thập kết quả dự báo thời tiết.

* 3-hour forecast 5 days: trả về 40 kết quả dự báo, là các bước cách nhau 3 giờ (ví dụ 1h30 gọi thì sẽ báo 4h, 7h,... )
* forecast air pollution: trả về 90 kết quả dự báo, cách nhau 1 giờ ( ví dụ 1h30 gọi thì trả về 1h, 2h)

## 4. Tính toán API call.

Giới hạn 60 requests / 1 phút, tức 1 requests 1 giây
* Thời tiết hiện tại 120s gọi một lần (54 requests)
* Ô nhiễm không khí 120s gọi một lần (54 requests)
* Dự báo nhiệt độ, 1 giờ gọi một lần:
  * xử lý trùng lặp thế nào? ví dụ
    * lần 1: 1, 4, 7, 10, 13, 16
    * lần 2: 2, 5, 8, 11, 14, 17
    * lần 3: 3, 6, 9, 12, 15, 18
    * Lần 4: 4, 7, 10, 13, 16, 19

  * Xử lý: 
    * chỉ lưu trữ dữ liệu chưa xảy ra, vì vậy, cần có bước xóa đi dữ liệu cũ bằng cách so sánh với thời gian hiện tại. 
    * Lần 4 đã bị trùng với lần 1 --> thay thế toàn bộ lần 1 bằng lần 4. 
    * Như vậy sẽ đảm bảo dữ liệu dự báo là dữ liệu mới nhất và không có trong quá khứ
    

* Dự báo ô nhiễm không khí, 1 giờ gọi một lần:
  * Vì theo giờ, nên chỉ cần thay thế toàn bộ là đủ. ( có cơ chế kiểm tra thời gian để xóa cũng là một ý)


# III. Kafka producer.

## 1. Xác định cấu trúc tuần tự hóa.

Là xác định các file .avsc, vì dữ liệu đưa vào topic cần được tuần tự hóa để tối ưu, và avro schema là lựa chọn tốt.




### Dữ liệu thời tiết hiện tại.

https://api.openweathermap.org/data/2.5/weather?lat=20.9755354&lon=105.857446545674&appid=72dc1092f8152fcd1935938246615de4&units=metric

{
  "coord": {
    "lon": 105.8574,
    "lat": 20.9755
  },
  "weather": [
    {
      "id": 800,
      "main": "Clear",
      "description": "clear sky",
      "icon": "01n"
    }
  ],
  "base": "stations",
  "main": {
    "temp": 14.03,
    "feels_like": 13.42,
    "temp_min": 14.03,
    "temp_max": 14.03,
    "pressure": 1017,
    "humidity": 74,
    "sea_level": 1017,
    "grnd_level": 1017
  },
  "visibility": 10000,
  "wind": {
    "speed": 1.75,
    "deg": 2,
    "gust": 1.87
  },
  "clouds": {
    "all": 0
  },
  "dt": 1735670305,
  "sys": {
    "type": 1,
    "id": 9308,
    "country": "VN",
    "sunrise": 1735688007,
    "sunset": 1735727178
  },
  "timezone": 25200,
  "id": 1581130,
  "name": "Hanoi",
  "cod": 200
}

Những cái quan trọng cần lấy:

{
  "coord": {
    "lon": 105.8574,
    "lat": 20.9755
  },
  "weather": [
    {
      "description": "clear sky"
    }
  ],
  "main": {
    "temp": 14.03,
    "feels_like": 13.42,
    "pressure": 1017,
    "humidity": 74
  },
  "visibility": 10000,
  "wind": {
    "speed": 1.75,
    "deg": 2,
    "gust": 1.87
  },
  "dt": 1735670305
}

### Ô nhiễm không khí hiện tại.

https://api.openweathermap.org/data/2.5/air_pollution?lat=20.9755354&lon=105.857446545674&appid=72dc1092f8152fcd1935938246615de4

{
  "coord": {
    "lon": 105.8574,
    "lat": 20.9755
  },
  "list": [
    {
      "main": {
        "aqi": 5
      },
      "components": {
        "co": 3952.03,
        "no": 59.9,
        "no2": 76.77,
        "o3": 0,
        "so2": 29.8,
        "pm2_5": 321.76,
        "pm10": 374.86,
        "nh3": 30.15
      },
      "dt": 1735674374
    }
  ]
}


### Dự báo nhiệt độ 5 ngày tới (3hours)
tách ra

