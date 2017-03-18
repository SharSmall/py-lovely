import model

class Friendship(model.Model):

    FIELDS = ['fbid', 'friend_id'] 
    TABLE = 'friendship'
