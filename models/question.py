class Question:
    def __init__(
        self,
        id,
        question,
        option1,
        option2,
        option3,
        option4,
        answer,
        category
    ):
        self.id = id
        self.question = question
        self.option1 = option1
        self.option2 = option2
        self.option3 = option3
        self.option4 = option4
        self.answer = answer
        self.category = category