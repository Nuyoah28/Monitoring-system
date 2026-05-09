 推流：
 ffmpeg -re -stream_loop -1 -i D:\projectFBX\城市智眼\Monitoring-system\ebike.mp4 -c copy -f flv rtmp://123.56.248.17:1935/live/raw


ffmpeg -re -stream_loop -1 -i D:\projectFBX\城市智眼\Monitoring-system\fall.mp4 -c copy -f flv rtmp://123.56.248.17:1935/live/raw