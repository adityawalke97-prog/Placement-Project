class Resume:
    def __init__(
        self,
        id,
        user_id,
        name,
        email,
        mobile,
        objective,
        education,
        skills,
        projects,
        certifications
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.email = email
        self.mobile = mobile
        self.objective = objective
        self.education = education
        self.skills = skills
        self.projects = projects
        self.certifications = certifications