class UserNews:
    def __init__(self, id, user_id, news_id, is_favorite=True):
        self.id = id
        self.user_id = user_id
        self.news_id = news_id
        self.is_favorite = is_favorite
