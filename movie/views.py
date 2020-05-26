from django.shortcuts import render
import json
from django.views.generic.base import View
from django.http import HttpResponse
from elasticsearch import Elasticsearch
from datetime import datetime
import redis

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
        top_num = int(request.GET.get('q', '5'))  # 获取url中参数s的值
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=top_num)
        re_datas=[]
        for topn in topn_search:
            data={}
            data["name"]=topn
            data["value"]=redis_cli.zscore("search_keywords_set",topn)
            re_datas.append(data)
        return HttpResponse(json.dumps(re_datas), content_type="application/json")

class SuggestView(View):
    def get(self,request):
        key_words = request.GET.get('q', '')  # 获取url中参数s的值
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
        print(key_words)
        source=request.GET.get("source", "")
        period=request.GET.get("period", "")
        sort=request.GET.get("sort", "")
        p1=request.GET.get("p1", "")
        p2 = request.GET.get("p2", "")
        category = request.GET.get("category", "")
        area = request.GET.get("area", "")
        size = request.GET.get("size", "")
        redis_cli.zincrby("search_keywords_set", 1, key_words)  # 该key_words的搜索记录+1
        douban_count = redis_cli.get("douban_count")
        try:
            source = int(source)
        except:
            source = 0
        if size=="":
            try:
                p1 = int(p1)
            except:
                p1 = 1
            try:
                p2 = int(p2)
            except:
                p2 = 10
            sql_should=[]
            sql_should.append({"match": {"title": key_words}})
            sql_should.append({"match": {"description": key_words}})
            sql_should.append({"match": {"director": key_words}})
            sql_should.append({"match": {"performer": key_words}})
            print(sql_should)
            sql_must=[]
            if source==1:
                sql_must.append({"match": {"resource": "豆瓣"}})
            elif source==2:
                sql_must.append({"match": {"resource": "电影天堂"}})
            if period!="":
                sql_must.append({"match": {"year": period}})
            if category!="":
                sql_must.append({"match": {"categories": category}})
            if area!="":
                sql_must.append({"match": {"area": area}})
            start_time = datetime.now()
            sql_must.append({"bool":{"should":sql_should}})
            print(sql_must)
            # 根据关键字查找
            response = client.search(
                index="movie",
                body={
                    "query": {
                        "bool": {
                            "must":sql_must
                        }
                    },
                    "from": (p1 - 1) * p2,
                    "size": p2,
                    # 对关键字进行高光标红处理
                    "highlight": {
                        "pre_tags": ['<span color="red">'],
                        "post_tags": ['</span>'],
                        "fields": {
                            "title": {},
                            "description": {},
                            "director":{},
                            "performer":{}
                        }
                    }
                }
            )
            print(response)
            end_time = datetime.now()
        else:
            sql_must = []
            source = int(source)
            if source == 1:
                sql_must.append({"match": {"resource": "豆瓣"}})
            elif source == 2:
                sql_must.append({"match": {"resource": "电影天堂"}})
            if category!="":
                sql_must.append({"match": {"categories": category}})
            size=int(size)
            start_time = datetime.now()
            # 根据关键字查找
            response = client.search(
                index="movie",
                body={
                    "query": {
                        "bool": {
                            "must": sql_must
                        }
                    },
                    "size": size
                }
            )
            print(response)
            end_time = datetime.now()
        hit_list = []
        total_nums = response["hits"]["total"]['value']
        for hit in response["hits"]["hits"]:
            hit_dict = {}
            if size=="":
                if "description" in hit["highlight"]:
                    hit_dict["description"] = "".join(hit["highlight"]["description"])
                else:
                    hit_dict["description"] = hit["_source"]["description"]
                if "title" in hit["highlight"]:
                    hit_dict["title"] = "".join(hit["highlight"]["title"])
                else:
                    hit_dict["title"] = hit["_source"]["title"]
                if "performer" in hit["highlight"]:
                    hit_dict["performer"] = "".join(hit["highlight"]["performer"])
                else:
                    hit_dict["performer"] = hit["_source"]["performer"]
                if "director" in hit["highlight"]:
                    hit_dict["director"] = "".join(hit["highlight"]["director"])
                else:
                    hit_dict["director"] = hit["_source"]["director"]
            else:
                hit_dict["description"] = hit["_source"]["description"]
                hit_dict["title"] = hit["_source"]["title"]
                hit_dict["performer"] = hit["_source"]["performer"]
                hit_dict["director"] = hit["_source"]["director"]
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
            hit_dict["categories"] = hit["_source"]["categories"]
            hit_dict["writer"] = hit["_source"]["writer"]
            hit_dict["pub"] = hit["_source"]["pub"]
            hit_dict["url"] = hit["_source"]["url"]
            hit_dict["score"] = hit["_score"]
            hit_list.append(hit_dict)
        last_seconds = (end_time - start_time).total_seconds()
        body = {}
        body["total"] = total_nums
        body["movieList"] = hit_list
        data = {"status": 0, "costTime": last_seconds,
                "douban_count": douban_count, "resultBody": body}
        return HttpResponse(json.dumps(data), content_type="application/json")