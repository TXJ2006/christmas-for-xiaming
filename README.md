# 江小唐给夏鸣的圣诞祝福

一封可以点亮的圣诞来信。原创 Canvas 冬日树景、飘雪、圣诞音乐盒与完整中文祝福。

公开访问：https://txj2006.github.io/christmas-for-xiaming/

直接打开 `index.html` 即可浏览，无需安装依赖。音乐默认关闭，点击「听见圣诞」后播放。

支持手机、桌面、键盘操作及系统减少动态效果偏好。不收集访客数据。

首页音乐为公版曲目 Jingle Bells 的程序合成音乐盒编排。彩蛋「一段小小的旧时光」是 28 秒的本地 MP4，采用原创微缩布景和合成配乐，无外部音频或图像依赖。

标题使用开源字体 Ma Shan Zheng 的本地字符子集，许可证见 `FONT-LICENSE.txt`。

### 重新渲染短片

```sh
blender -b --python-exit-code 1 -P film-source.py -- /tmp/winter-silent
python3 film-score.py /tmp/winter-score.wav
ffmpeg -i /tmp/winter-silent0001-0448.mp4 -i /tmp/winter-score.wav -c:v copy -c:a aac -b:a 112k -movflags +faststart winter-film.mp4
ffmpeg -ss 6 -i winter-film.mp4 -frames:v 1 -q:v 3 winter-film.jpg
```
