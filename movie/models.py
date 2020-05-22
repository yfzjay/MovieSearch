from django.db import models

# Create your models here.
from elasticsearch_dsl import DocType, Date, Completion, Keyword, Text, Integer

from elasticsearch_dsl.connections import connections
connections.create_connection(hosts=["112.126.58.87"])

class jobType(DocType):
    class Meta:# 设置index名称和document名称
        index = "51job"
        doc_type = "_doc"

    class Index:
        name = "51job"
        doc_type = "_doc"

    url = Keyword()  # 不分词，默认保留256个字符
    job_name = Text(
        analyzer="ik_max_word")  # “中华人民共和国国歌”拆分为“中华人民共和国,中华人民,中华,华人,人民共和国,人民,人,民,共和国,共和,和,国国,国歌”，会穷尽各种可能的组合；
    salary = Text(analyzer="ik_smart")  # 将“中华人民共和国国歌”拆分为“中华人民共和国,国歌”将“中华人民共和国国歌”拆分为“中华人民共和国,国歌”
    company = Text(analyzer="ik_max_word")
    job_position = Text(analyzer="ik_max_word")
    experience = Text(analyzer="ik_max_word")
    education = Text(analyzer="ik_max_word")
    number_of_people = Integer()
    published_time = Date()
    position_detail = Text(analyzer="ik_smart")
    position_type = Text(analyzer="ik_max_word")
    location = Text(analyzer="ik_max_word")
    company_detail = Text(analyzer="ik_max_word")

    suggest = Completion()  # 搜索建议

