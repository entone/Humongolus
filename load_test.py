from pymongo.connection import Connection
import logging
import humongolus as orm
import datetime
import humongolus.field as field
from slugify import slugify

conn = Connection()
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("humongolus")

orm.settings(logger=logger, db_connection=conn)

class Slug(field.Char):

    def clean(self, val, doc=None):
        if val: return slugify(val)
        return val

class S3Attachment(orm.EmbeddedDocument):
    filename = field.Char()

    @property
    def url(self):
        if self.filename:
            s3_url = config.AWS_S3_URL
            if s3_url[-1] == '/':
                s3_url = s3_url[:-1]
            return '/'.join([s3_url, self.filename])

class Mode(field.Choice):
    _choices = ['Live', 'Draft']

class Category(orm.Document):
    _db = "curiosity"
    _collection = "categories"
    _indexes = [
        orm.Index("slug", key=[("slug", 1)], unique=True),
    ]

    class Images(orm.EmbeddedDocument):
        icon = S3Attachment()
        thumbnail = S3Attachment()
        hero = S3Attachment()

    name = field.Char()
    slug = field.Char()
    images = Images()
    mode = Mode()

    def taxonomy(self):
        tax = [self.name]
        if self.parent:
            tax[:0] = self._get("parent")().taxonomy()

        return tax


class Entity(orm.Document):
    _db = "curiosity"
    _collection = "entities"
    _indexes = [
        orm.Index('name', key=[('s', 1)], unique=True),
        orm.Index('type', key=[('t', 1)]),
        orm.Index('categories', key=[('categories.link', 1)]),
    ]

    name = field.Char(dbkey='n')
    slug = field.Char(dbkey='s')
    type = field.Char(dbkey='t')
    extraction = field.Char()


class Image(orm.EmbeddedDocument):
    url = field.Char()
    type = field.Char()
    description = field.Char()
    width = field.Integer()
    height = field.Integer()


class Video(orm.EmbeddedDocument):
    url = field.Char()
    type = field.Char()
    description = field.Char()
    length = field.Float()


class CourseTag(orm.EmbeddedDocument):
    type = field.Char()
    weight = field.Float()
    name = field.Char()


class Price(orm.EmbeddedDocument):
    type = field.Char()
    amount = field.Float()
    added = field.Date()
    expires = field.Date()


class Provider(orm.Document):
    _db = "curiosity"
    _collection = "providers"

    external_id = field.Integer()
    name = field.Char()
    slug = Slug()
    url = field.Char()
    verified = field.Boolean()
    images = orm.List(type=Image)
    description = field.Char()

class Sources(field.Choice):
    _choices = ['none', 'nlp', 'tag', 'category', 'metakeyword', 'entity']

class Keyword(orm.EmbeddedDocument):
    name = field.Char()
    slug = field.Char()
    source = Sources(default='none')


class EmbeddedEntity(orm.EmbeddedDocument):
    name = field.Char()
    entity = field.DocumentId(type=Entity)
    method = field.Char()
    relevance = field.Float()
    verified = field.Boolean(default=False)


class EmbeddedCategory(orm.EmbeddedDocument):
    slug = field.Char()
    probability = field.Float(default=0.0)
    method = field.Char()
    verified = field.Boolean(default=False)


class CourseFilter(orm.EmbeddedDocument):
    name = field.Char()
    value = field.Field()


class ESKeyword(orm.Document):
    _db = "curiosity"
    _collection = "keywords"
    _indexes = [
        orm.Index("categories", key=[("slug", 1)], unique=True),
    ]

    slug = field.Char()


class SocialMedia(orm.EmbeddedDocument):
    twitter = field.Char()
    facebook = field.Char()
    linkedin = field.Char()
    google = field.Char()
    email = field.Char()
    blog = field.Char()


class Source(orm.Document):
    _db = "curiosity"
    _collection = "sources"

    class Fact(orm.EmbeddedDocument):
        name = field.Char()
        value = field.Char()

    class About(orm.EmbeddedDocument):
        description = field.Char()
        url = field.Char()
        video = Video()
        image = Image()

    name = field.Char()
    slug = Slug()
    description = field.Char()
    url = field.Char()
    logo = Image()
    filters = orm.List(type=CourseFilter)
    facts = orm.List(type=Fact)
    about = About()
    social = SocialMedia()
    tagline = field.Char()
    location = field.Char()


class CourseOccurence(orm.EmbeddedDocument):
    duration = field.Char()
    start = field.Date()
    end = field.Date()
    ace_eligible = field.Boolean(default=False)
    certificate_eligible = field.Boolean(default=False)


class Instructor(orm.Document):
    _db = "curiosity"
    _collection = "instructors"

    external_id = field.Integer()
    title = field.Char()
    first_name = field.Char()
    middle_name = field.Char()
    last_name = field.Char()
    suffix = field.Char()
    full_name = field.Char()

    description = field.Char()

    images = orm.List(type=Image)
    social = SocialMedia()


class InstructorLink(orm.EmbeddedDocument):
    link = field.DocumentId(type=Instructor)
    name = field.Char()


class ProviderLink(orm.EmbeddedDocument):
    link = field.DocumentId(type=Provider)
    name = field.Char()


class CuriosityRanking(orm.EmbeddedDocument):
    rank = field.Float(default=1)


class Modality(field.Choice):
    _choices = ['in-person', 'online', 'video', 'interactive', 'streaming']

class Course(orm.Document):
    _db = "curiosity"
    _collection = "courses"
    _indexes = [
        orm.Index("slug", key=[("slug", 1)], unique=True, drop_dups=True),
        orm.Index(
            "external", key=[("external_id", 1), ("source", 1)], unique=True, drop_dups=True),
        orm.Index("categories", key=[('categories.slug', 1)]),
        orm.Index("entities", key=[('entities.entity', 1)]),
        orm.Index("keywords", key=[('keywords.slug', 1)]),
        orm.Index("source", key=[("source", 1)]),
    ]

    external_id = field.Char()
    # where is this class from eg; Coursera
    source = field.DocumentId(type=Source)
    name = field.Char()
    slug = Slug()
    description = field.Char()
    short_description = field.Char()
    faq = field.Char()
    published = field.Boolean(default=True)
    featured = field.Boolean(default=False)

    modality = Modality(default='online')
        
    popularity = field.Integer(default=1)
    skill_level = field.Integer(default=0)
    rating = field.Float(default=1)
    ranking = CuriosityRanking()
    location = field.Geo()
    duration = field.Integer(default=0)

    url = field.Char()
    instructors = orm.List(type=InstructorLink)
    language = field.Char()
    workload = field.Char()
    occurences = orm.List(type=CourseOccurence)
    images = orm.List(type=Image)
    videos = orm.List(type=Video)
    keywords = orm.List(type=Keyword)
    entities = orm.List(type=EmbeddedEntity)
    providers = orm.List(type=ProviderLink)
    categories = orm.List(type=EmbeddedCategory)
    prices = orm.List(type=Price)
    filters = orm.List(type=CourseFilter)


[c for c in Course.find().limit(5000)]