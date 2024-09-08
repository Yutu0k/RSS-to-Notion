# RSS-to-Notion

将RSS源导入Notion进行整理，提供URL进行阅读，并且利用Github Action自动更新RSS内容

![source.png](0_Docs/source.png)

支持[简悦](https://github.com/Kenshin/simpread)使用同一数据库，更好管理阅读源

## How to Use?

1. 将下列[模板](https://www.notion.so/Notion-RSS-7baa9624198e487eb121ca3b2e07f354?pvs=21)保存到自己的Notion中（不要修改Database属性）
2. 将本项目Fork到自己的`Github`中
3. 创建`Notion Integration`并且关联到Notion页面（创建完成后会给出API Key）
4. 在`Github Settings/Secrets and variables/Actions` 中添加三个环境变量（数据库id怎么获得可以问问度娘）
    
    ```yaml
    NOTION_API_KEY
    NOTION_READING_DATABASE_ID   # Notion RSS.Entries数据库id
    NOTION_URL_DATABASE_ID       # Notion RSS.Feed数据库id
    ```
    
5. （可选）更改更新频率
    
    更改`.github/workflows/main.yml` 中`- cron` 行，支持[cron表达式](https://crontab.guru/#0_*_*_*_*)
    
6. 在`Github Actions` 界面手动run workflow一次，后面就会自动更新

## Features

- 在Notion数据库中管理RSS源（支持添加`Disable标签`控制是否更新和`Tags标签`控制添加内容的Tag）
- 利用Notion管理RSS Entries（例如关键词、文章信息、标签等）
- 定时更新

## Acknowledgement

- https://github.com/Key033/RSS2Notion
- https://github.com/rainyear/dailybot