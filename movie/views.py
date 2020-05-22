from django.shortcuts import render
import json
from django.shortcuts import render
from django.views.generic.base import View
from movie.models import jobType
from django.http import HttpResponse
from elasticsearch import Elasticsearch
from datetime import datetime
import redis
# Create your views here.

client = Elasticsearch(hosts=["127.0.0.1"])

pool = redis.ConnectionPool(host='127.0.0.1', port=6379, decode_responses=True)
redis_cli = redis.Redis(connection_pool=pool)

response1 = client.search(
    index="movie",
    body={
        "query": {
            "multi_match": {
                "query": "豆瓣",
                "fields": ["resource"]
            }
        }
    }
)

redis_cli.set("douban_count",response1['hits']['total']['value'])

class TopView(View):
    def get(self,request):
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)
        return HttpResponse(json.dumps(topn_search), content_type="application/json")

class SuggestView(View):
    def get(self,request):
        key_words = request.GET.get('s', '')  # 获取url中参数s的值
        print(key_words)
        re_datas = []
        response = client.search(
            index="movie",
            body={
                "_source": "title",
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ["title", "description"]
                    }
                },
                "size": 5
            }
        )
        for hit in response["hits"]["hits"]:
            re_datas.append(hit["_source"]["title"])
        return HttpResponse(json.dumps(re_datas), content_type="application/json")

class SearchView(View):
    def get(self,request):
        key_words = request.GET.get("q", "")
        # 获取当前选择搜索的范围
        # s_type = request.GET.get("s_type", "51job")

        redis_cli.zincrby("search_keywords_set", 1, key_words)  # 该key_words的搜索记录+1
        print()
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)
        #topn_search = [item.decode('utf8') for item in topn_search]
        page = request.GET.get("p", "1")
        try:
            page = int(page)
        except:
            page = 1
        # 从redis查看该类数据总量
        douban_count = redis_cli.get("douban_count")

        start_time = datetime.now()
        # 根据关键字查找
        response = client.search(
            index="movie",
            body={
                "query": {
                    "multi_match": {
                        "query": key_words,
                        "fields": ["title", "description"]
                    }
                },
                "from": (page - 1) * 10,
                "size": 10,
                # 对关键字进行高光标红处理
                "highlight": {
                    "pre_tags": ['<span class="keyWord">'],
                    "post_tags": ['</span>'],
                    "fields": {
                        "title": {},
                        "description": {},
                    }
                }
            }
        )
        print(response)
        end_time = datetime.now()
        last_seconds = (end_time - start_time).total_seconds()
        total_nums = response["hits"]["total"]['value']
        if (total_nums % 10) > 0:
            page_nums = int(total_nums / 10) + 1
        else:
            page_nums = int(total_nums / 10)
        hit_list = []
        for hit in response["hits"]["hits"]:
            hit_dict = {}
            print(hit)
            if "description" in hit["highlight"]:
                hit_dict["description"] = "".join(hit["highlight"]["description"])
            else:
                hit_dict["description"] = hit["_source"]["description"]
            if "title" in hit["highlight"]:
                hit_dict["title"] = "".join(hit["highlight"]["title"])[:500]
            else:
                hit_dict["title"] = hit["_source"]["title"][:500]

            hit_dict["pub"] = hit["_source"]["pub"]
            hit_dict["website"] = hit["_source"]["website"]
            hit_dict["year"] = hit["_source"]["year"]
            hit_dict["movie_score"] = hit["_source"]["score"]
            hit_dict["area"] = hit["_source"]["area"]
            hit_dict["resource"] = hit["_source"]["resource"]
            hit_dict["image"] = hit["_source"]["image"]
            hit_dict["imdb"] = hit["_source"]["imdb"]
            hit_dict["star"] = hit["_source"]["star"]
            hit_dict["time"] = hit["_source"]["time"]
            hit_dict["commentCount"] = hit["_source"]["commentCount"]
            hit_dict["better"] = hit["_source"]["better"]
            hit_dict["alias"] = hit["_source"]["alias"]
            hit_dict["language"] = hit["_source"]["language"]
            hit_dict["director"] = hit["_source"]["director"]
            hit_dict["categories"] = hit["_source"]["categories"]
            hit_dict["writer"] = hit["_source"]["writer"]
            hit_dict["performer"] = hit["_source"]["performer"]
            hit_dict["pub"] = hit["_source"]["pub"]
            hit_dict["score"] = hit["_score"]
            hit_list.append(hit_dict)
        data={"page": page,"all_hits": hit_list,"key_words": key_words,
              "total_nums": total_nums,"page_nums": page_nums,"last_seconds": last_seconds,
              "douban_count": douban_count,"topn_search": topn_search}
        return HttpResponse(json.dumps(data), content_type="application/json")