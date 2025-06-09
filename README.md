# facebook_scraper

## Mục đích
Công cụ này dùng để crawl (thu thập) bài viết và bình luận từ các fanpage Facebook, đồng thời tải về toàn bộ hình ảnh trong bài viết và bình luận.

## Tính năng
- Crawl toàn bộ bài viết từ danh sách fanpage cho trước.
- Lấy tối đa 100 bình luận đầu tiên cho mỗi bài viết (có thể tùy chỉnh).
- Tải toàn bộ ảnh trong bài viết và bình luận về cùng một thư mục.
- Lưu dữ liệu bài viết và bình luận vào file JSON duy nhất (`data/json/posts.json`).

## Cấu trúc dữ liệu đầu ra
Mỗi bài viết sẽ có dạng:
```json
{
  "post_content": "Nội dung bài viết...",
  "image_paths": ["data/image/xxx.jpg", ...],
  "feedback_id": "...",
  "creation_time": 1234567890,
  "total_reactions": 100,
  "reactions_detail": {"Like": 90, "Love": 10},
  "share_count": "5",
  "comment_count": 10,
  "post_url": "https://www.facebook.com/...",
  "comments": [
    {
      "text": "Nội dung bình luận...",
      "image": "data/image/yyy.jpg"
    }
    // ...
  ]
}
```

## Hướng dẫn sử dụng

### 1. Chuẩn bị
- Cài đặt dependency:
```bash
pip install -r requirements.txt
```
- Chuẩn bị file `facebook_urls/page_urls.txt` chứa danh sách link fanpage, mỗi dòng một link.

### 2. Chạy chương trình
```bash
python facebook_scraper.py
```

### 3. Kết quả
- Dữ liệu bài viết và bình luận sẽ được lưu tại: `data/json/posts.json`
- Ảnh sẽ được tải về thư mục: `data/image/`

## Lưu ý
- Chỉ lưu ảnh có đuôi hợp lệ (.jpg, .png, .gif, ...)
- Mỗi bài viết chỉ lấy tối đa 100 bình luận đầu tiên (có thể tùy chỉnh).

## Tác giả
| MSSV      | Họ và Tên             |
|-----------|-----------------------|
| 22520467  | Nguyễn Duy Hoàng      |
| 22520460  | Hà Huy Hoàng          |
| 22520490  | Đặng Vĩnh Hội         |
| 22520452  | Nguyễn Hoàng Hiệp     |

## Repo lấy ý tưởng từ:
https://github.com/tlyu0419/facebook_crawler  
**Author:** TENG-LIN YU  
**Email:** tlyu0419@gmail.com  
**Facebook:** https://www.facebook.com/tlyu0419  
**PYPI:** https://pypi.org/project/facebook-crawler/  
**Github:** https://github.com/TLYu0419/facebook_crawler