class GroupManager(object):
    def __init__(self):
        self.group = {}

    def register(self, user):
        group_name = user.get_argument("group_name")
        user_id = int(user.get_argument("user_id"))
        print(group_name,user_id)
        if group_name in self.group.keys():
            self.group[group_name][user_id] = user
        else:
            user_ws = {user_id: user}
            self.group[group_name]= user_ws
        print(self.group)


    def unregister(self, user):
        group_name = user.get_argument("group_name")
        user_id = user.get_argument("user_id")

        try:
            self.group[group_name].pop(user_id)
        except KeyError:
            pass

    def get_user(self, user_id, group_name):
        return self.group[group_name][user_id]

    def get_group_user(self, group_name):
        return self.group[group_name].values()

    def get_all_user(self):
        all_users = []
        for k, v in self.group.items():
            all_users.extend(v.values())

        return all_users


class SenderMixin(object):
    def broadcast(self, group, message):
        for user in group:
            user.write_message(message)

    def private_message(self, user, message):
        user.write_message(message)
