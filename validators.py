
import config

class Validator(object):
    def validate(self, data):
        try:
            message_type = data["message_type"]
            if not message_type in config.MESSAGE_TYPE:
                return {"detail": "invalid message_type"}
        except:
            return {"detail": "empty message_type"}

        if not "args" in data.keys():
            return {"detail": "no args given"}

        if not "message" in data.keys():
            return {"detail": "no message given"}

        try:
            send_type = data["send_type"]
            if not send_type in config.SEND_TYPE:
                return {"detail": "invalid send_type"}
            elif send_type == "private":
                if not "send_user_id" in data["args"].keys():
                    return {"detail": "empty send_user_id"}

                if not "send_group_name" in data["args"].keys():
                    return {"detail": "empty send_group_name"}
            elif send_type == "group":
                if not "send_group_name" in data["args"].keys():
                    return {"detail": "empty send_group_name"}

        except:
            return {"detail": "empty send_type"}

        return True
