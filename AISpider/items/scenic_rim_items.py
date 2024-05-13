from scrapy import Field
from . import BaseItem

class ScenicRimItem(BaseItem):
    application_id = Field()
    category = Field()
    lodgement_date = Field()
    description = Field()
    status = Field()
    finalised_date = Field()
    officer = Field()
    address = Field()
    names = Field()
    documents = Field()

    class Meta:
        table = 'scenic_rim'
        unique_fields = ['application_id', ]