from mongoengine import *

class Keyword(EmbeddedDocument):
    name = StringField()
    slug = StringField()
    source = StringField(
        choices=['none', 'nlp', 'tag', 'category', 'metakeyword', 'entity'], default='none')


class CourseOccurence(EmbeddedDocument):
    duration = StringField()
    start = DateTimeField()
    end = DateTimeField()
    ace_eligible = BooleanField(default=False)
    certificate_eligible = BooleanField(default=False)


class CuriosityRanking(EmbeddedDocument):
    rank = FloatField(default=1)


class CourseFilter(EmbeddedDocument):
    name = StringField()
    value = StringField()


class EmbeddedCategory(EmbeddedDocument):
    slug = StringField()
    probability = FloatField(default=0.0)
    method = StringField()
    verified = BooleanField(default=False)


class EmbeddedEntity(EmbeddedDocument):
    name = StringField()
    entity = ObjectIdField()
    method = StringField()
    relevance = FloatField()
    verified = BooleanField(default=False)


class ProviderLink(EmbeddedDocument):
    link = ObjectIdField()
    name = StringField()


class InstructorLink(EmbeddedDocument):
    link = ObjectIdField()
    name = StringField()


class SocialMedia(EmbeddedDocument):
    twitter = StringField()
    facebook = StringField()
    linkedin = StringField()
    google = StringField()
    email = StringField()
    blog = StringField()

class Image(EmbeddedDocument):
    url = StringField()
    type = StringField()
    description = StringField()
    width = IntField()
    height = IntField()


class Video(EmbeddedDocument):
    url = StringField()
    type = StringField()
    description = StringField()
    length = FloatField()


class CourseTag(EmbeddedDocument):
    type = StringField()
    weight = FloatField()
    name = StringField()


class Price(EmbeddedDocument):
    type = StringField()
    amount = FloatField()
    added = DateTimeField()
    expires = DateTimeField()


class Source(Document):
    class Fact(EmbeddedDocument):
        name = StringField()
        value = StringField()

    class About(EmbeddedDocument):
        description = StringField()
        url = StringField()
        video = EmbeddedDocumentField(Video)
        image = EmbeddedDocumentField(Image)

    name = StringField()
    slug = StringField()
    description = StringField()
    url = StringField()
    logo = EmbeddedDocumentField(Image)
    filters = ListField(EmbeddedDocumentField(CourseFilter))
    facts = ListField(EmbeddedDocumentField(Fact))
    about = EmbeddedDocumentField(About)
    social = EmbeddedDocumentField(SocialMedia)
    tagline = StringField()
    location = StringField()


class Course(Document):
    meta = {
        'collection': 'courses'
    }

    external_id = StringField()
    # where is this class from eg; Coursera
    source = ObjectIdField()
    name = StringField()
    slug = StringField()
    description = StringField()
    short_description = StringField()
    faq = StringField()
    published = BooleanField(default=True)
    featured = BooleanField(default=False)

    modality = StringField(
        choices=['in-person', 'online', 'video', 'interactive', 'streaming'], default='online')
    popularity = IntField(default=1)
    skill_level = IntField(default=0)
    rating = FloatField(default=1)
    ranking = EmbeddedDocumentField(CuriosityRanking)
    location = ListField()
    duration = IntField(default=0)

    url = StringField()
    instructors = ListField(EmbeddedDocumentField(InstructorLink))
    language = StringField()
    workload = StringField()
    occurences = ListField(EmbeddedDocumentField(CourseOccurence))
    images = ListField(EmbeddedDocumentField(Image))
    videos = ListField(EmbeddedDocumentField(Video))
    keywords = ListField(EmbeddedDocumentField(Keyword))
    entities = ListField(EmbeddedDocumentField(EmbeddedEntity))
    providers = ListField(EmbeddedDocumentField(ProviderLink))
    categories = ListField(EmbeddedDocumentField(EmbeddedCategory))
    prices = ListField(EmbeddedDocumentField(Price))
    filters = ListField(EmbeddedDocumentField(CourseFilter))

connect('curiosity')
[c for c in Course.objects[:5000]]