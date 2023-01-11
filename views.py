import re
from tkinter import PAGES
from django.shortcuts import redirect, render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
import sys
from engine.utils import dictfetchall, images_to_pdf
    
class Doctype(APIView):
    
    def get(self, request, format=None):
        try:
            with connection.cursor() as cursor:
                    cursor.execute("""
                        select id, doc_id, change_doc_name, pred_id  from document_type order by doc_id
                    """)
                    result = dictfetchall(cursor)
    
            return Response({'success': True, 'result': result})
        except:
            return Response({'success': False, 'result': []})


        
class Cif_document(APIView):
    
    def get(self, request, format=None):
        try:
            with connection.cursor() as cursor:
                    cursor.execute("""
                        select * from (select * from scan_cif where review_flg = 0) where rownum = 1
                    """)
                    result = dictfetchall(cursor)
            return Response({'success': True, 'result': result})
        except:
            return Response({'success': False, 'result': []})

class Doc_list(APIView):
    def get(self, request, format=None):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                                select doc_date, cif_id from scan_cif 
                                
                            """)
                result = dictfetchall(cursor)
            return Response({'success': True, 'result': result})
        except:
            return Response({'success': False, 'result': []})
                
class Sol(APIView):
    def get(self, request, format=None):
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                                select sol_id, sol_desc from finacle.sol@BIRAC
                            """)
                result = dictfetchall(cursor)
            
            return Response({'success': True, 'result': result})
        except:
            return Response({'success': False, 'result': []})


class CifDocumentCheck(APIView):
    
    def get(self, request, format = None):
        try:
            
            with connection.cursor() as cursor:
                cursor.execute("""
                             select * from  (select t1.scan_sol_id, t2.file_path from cif_document t1
                                inner join scan_sol t2 on t1.scan_sol_id = t2.id
                                where t1.checking = 0 and t1.review_omniscan = 0
                             ) where rownum = 1
                        """)
                
                result = dictfetchall(cursor)
                
                id = result[0]['scan_sol_id']
                file_path = result[0]['file_path']
                
               
                cursor.execute("""
                           update cif_document set checking = 1 where scan_sol_id = :id
                        """, {'id': id}) 
                
                
                cursor.execute("""
                            select distinct t1.id, t1.page_number, t1.temp_match, t1.doc_type_id, t1.pred_id, t2.change_doc_name, TO_CHAR(t1.cropimage) as cropimage, foracid from sol_document t1
                            inner join document_type t2 on t1.doc_type_id = t2.id and t2.pred_id = t1.pred_id where scan_sol_id = :id  
                            order by page_number, temp_match
                        """, {'id': id})
                
               
                
                result = dictfetchall(cursor)
                
                return Response({'success': True, 'id': id, 'file_path': file_path, 'sol_document': result})
        except Exception as e:
            
            return Response({'success': False, 'result': []})
                
     
    # def delete(self, request, pk, format = None):
    #     try:
    #         with connection.cursor() as cursor:
    #             # print(pk)
    #             cursor.execute("""
    #                         delete from sol_document where id = :id  
    #                     """, {'id': pk})
                
    #             return Response(status=status.HTTP_204_NO_CONTENT)
                        
    def post(self, request, format = None):
        try:
            userid = request.query_params.get('userid') or request.data.get("userid")
            cifdocument = request.query_params.get('cifdocument') or request.data.get("cifdocument")
           
            # print(userid)
            print(cifdocument)
           
            images_to_pdf(userid, cifdocument)


            with connection.cursor() as cursor:
                
                cursor.execute("""
                        select id, dms_type_name, pred_id  from document_type
                    """)
                
                doctype = dictfetchall(cursor)
                
                button_left = 0
                button_right = 0
    
                cifdocument.sort(key = lambda x: x['page_number'])
                a = cifdocument
                for i in range(len(a)):
                    a[i]['dms_type_name'] = [x['dms_type_name'] for x in doctype if x['id'] == a[i]['doc_type_id'] and x['pred_id'] == a[i]['pred_id']][0]
                
                for i in range(len(a)):
                    if i == 0:
                        button_left = 1
                        button_right = 0
                    elif i == len(a) - 1:
                        if a[i - 1]['dms_type_name'] == a[i]['dms_type_name']:
                            button_left = 0
                            button_right = 1
                        else:
                            button_left = 1
                            button_right = 0
                    elif a[i - 1]['dms_type_name'] == a[i]['dms_type_name'] and a[i]['dms_type_name'] == a[i + 1]['dms_type_name'] and i + 1 < len(a):
                        button_left = 0
                        button_right = 0
                    elif a[i - 1]['dms_type_name'] == a[i]['dms_type_name'] and a[i]['dms_type_name'] != a[i + 1]['dms_type_name'] and i + 1 < len(a):
                        button_left = 0
                        button_right = 1
                    else:
                        button_left = 1
                        button_right = 0
                    
                    # print(button_left)
                    dms_type_name = [x['dms_type_name'] for x in doctype if x['id'] == a[i]['doc_type_id'] and x['pred_id'] == a[i]['pred_id']][0]
                    if a[i]['foracid'] is None:
                        a[i]['foracid'] = 0
                    
                  
                    cursor.execute("""
                            insert into omniscan (id, page, doctype, button_left, button_right, foracid) values(:id, :page, :doctype, :button_left, :button_right, :foracid)
                        """, {'id': userid, 'page': i + 1, 'doctype': dms_type_name, 'button_left': button_left, 'button_right': button_right, 'foracid': a[i]['foracid']})
                    
                return Response({'success': True, 'result': []})
            
        except Exception as e:
            
            return Response({'success': False, 'result': []})
        

class DocumentCheck(APIView):
    
    def post(self, request, format = None):
        try:
            with connection.cursor() as cursor:
                id = request.query_params.get('id') or request.data.get("id")
                doctype_id = request.query_params.get('doctype_id') or request.data.get("doctype_id")
                pred_id = request.query_params.get('pred_id') or request.data.get("pred_id")
                
		                
                cursor.execute("""
                                select t1.id as ocr_id, t3.id as key, t3.field_name, t3.id as field_id, t1.detected_value, t1.crop_path as crop_image, t1.label_value
                                from (select * from ocr where sol_document_id = :id) t1 
                                right outer join docs_fields t2 on t1.field_id = t2.field_id
                                inner join ocr_field t3 on t2.field_id = t3.id
                                where t2.doc_type_id = :doctype_id and t2.doc_type_pred_id = :pred_id
                                order by t3.id
                            """, {'id': id, 'doctype_id': doctype_id, 'pred_id': pred_id})
                
                result = dictfetchall(cursor)
                for x in result:
                    
                    if x['crop_image'] is not None:
                        path = "https://smartdocs.golomtbank.local{}".format(x['crop_image'])
                        x['crop_image'] = path
                        
                cursor.execute("""
                              select * from fields where id is not NULL
                            """)
                

                ocr_field = dictfetchall(cursor)
                
                cursor.execute("""
                              select FIELD_ID, LABEL_VALUE from category_fields
                            """)
                
                
                category_fields = dictfetchall(cursor)
                
            return Response({'success': True, 
                             'result_ocr' : result, 
                             'ocr_field': ocr_field,
                             'category_fields': category_fields
                             })
            
        except Exception as e:
            
            return Response({'success': False, 'result': []})
        

        
class Document_ocr(APIView):
    
     def post(self, request, format = None):
        try:
            domain = request.query_params.get('domain') or request.data.get("domain")
            ocr_id = request.query_params.get('ocr_id') or request.data.get("ocr_id")
            crop_flag = request.query_params.get('crop_flag') or request.data.get("crop_flag")
            detected_value = request.query_params.get('detected_value') or request.data.get("detected_value")


            
            with connection.cursor() as cursor:
                
                cursor.execute("""
                             update ocr 
                             set review_flg = 1,
                                crop_flag = :crop_flag,
                                ocr_date = SYSDATE,
                                domain = :domain
                             where id = :ocr_id
                        """,  {'domain': domain, 'crop_flag' : crop_flag, 'ocr_id': ocr_id})
                
                
            return Response({'success': True, 'result': []})
        except:
            return Response({'success': False, 'result': []})
    
class CifCheck(APIView):
     def post(self, request, format = None):
        try:
            person_id = request.query_params.get('person_id') or request.data.get("person_id")
            with connection.cursor() as cursor:
                
                
                cursor.execute("""
                             select orgkey as cif_id from finacle.accounts@BIRAC where strfield12 = :person_id
                            """,  {'person_id': person_id})
                
                result = dictfetchall(cursor)
                if len(result) == 0:
                    cursor.execute("""
                                select cif_id from finacle.gam_accounts@BIRAC where foracid = :person_id
                                """,  {'person_id': person_id})
                    
                    result = dictfetchall(cursor)
                
                
            return Response({'success': True, 'cif': result[0]['cif_id']})
        except:
            return Response({'success': False, 'cif': ""})


class FileUpload(APIView):
    
    def post(self, request, format = None):
        try:
            domain = request.query_params.get('domain') or request.data.get("domain")
            sol = request.query_params.get('sol') or request.data.get("sol")
            filenames = request.query_params.get('filenames') or request.data.get("filenames")
	    
		
            with connection.cursor() as cursor:
            	  
                cursor.execute("""
                                select sol_id, kpi_sol_address from finacle.sol@BIRAC where sol_id = :sol
                            """, {'sol': sol})
                
                result = dictfetchall(cursor)
                 
                region = 'УБ' if result[0]['kpi_sol_address'] == 'Ulaanbaatar'  else 'ОН'; 
                
                for filename in filenames:  
                    
                    cursor.execute("""
                                insert into scan_sol (ID, FILE_PATH, REPORTED_DATE, UPLOADED_DATE, EMP_DOMAIN, SOL_ID, REGION) values(:id, :filename, SYSDATE, SYSDATE, :domain, :sol, :region)
                                """,  {'id': filename[:-4],'filename': '/btg_data/uploaded_file/{}'.format(filename), 'domain': domain, 'sol': sol, 'region': region})
                    
                    cursor.execute("""
                                insert into cif_document (scan_sol_id) values(:id)
                                """,  {'id': filename[:-4]})
                    
                    cursor.execute("""
                                insert into status (id) values(:id)
                                """,  {'id': filename[:-4]})
                    
                    
                
            return Response({'success': True })
        except:
	    
            return Response({'success': False})
        
class Foracid(APIView):
     def post(self, request, format = None):
        try:
            cif = request.query_params.get('cif') or request.data.get("cif")
            userid = request.query_params.get('userid') or request.data.get("userid")
            with connection.cursor() as cursor:
                
                cursor.execute("""
                             select foracid from finacle.gam_accounts@BIRAC where cif_id = :cif
                            """,  {'cif': cif})
                
                result = dictfetchall(cursor)
                
                cursor.execute("""
                             update cif_document set cif_id = :cif where scan_sol_id = :userid
                            """,  {'cif': cif, 'userid': userid})
                
            return Response({'success': True, 'foracid': result})
        except:
            return Response({'success': False, 'foracid': ""})        
        
class Reporta(APIView):
    def get(self, request, format=None):
        try:
            # sol = request.query_params.get('sol') or request.data.get("sol")
            with connection.cursor() as cursor:
                cursor.execute("""
                                SELECT DISTINCT *
                                FROM BTG_HHHA.REPORT1
                              
                            """)
                result = dictfetchall(cursor)
            
            return Response({'success': True, 'result': result})
        except:
            return Response({'success': False, 'result': []})
        
class Reportb(APIView):
    
     def get(self, request, format = None):
        # sol = request.query_params.get('sol') or request.data.get("sol")
        try:
            with connection.cursor() as cursor:
                
                cursor.execute("""
                                SELECT DISTINCT C12 AS c0,
                                    C1 AS c1,
                                    C6 AS c2,
                                    C11 AS c3,
                                    C9 AS c4,
                                    C7 AS c5,
                                    C8 AS c6,
                                    C10 AS c7,
                                    C5 AS c8,
                                    C3 AS c9,
                                    C4 AS c10,
                                    C17 AS c11,
                                    C15 AS c12,
                                    C16 AS c13
                                FROM BTG_HHHA.REPORT2
                               
                            """)
                
                result = dictfetchall(cursor)
                
            return Response({'success': True, 'result': result })
        except:
            return Response({'success': False})
        
class Reportc(APIView):
    
     def get(self, request, format = None):
        # sol = request.query_params.get('sol') or request.data.get("sol")
        try:
            with connection.cursor() as cursor:
                
                cursor.execute("""
                                SELECT DISTINCT C3 AS c0,
                                    C27 AS c1,
                                    C12 AS c2,
                                    C21 AS c3,
                                    C6 AS c4,
                                    C16 AS c5,
                                    C8 AS c6,
                                    C18 AS c7,
                                    C20 AS c8,
                                    C10 AS c9,
                                    C25 AS c10,
                                    C14 AS c11,
                                    C19 AS c12,
                                    C17 AS c13,
                                    C22 AS c14,
                                    C23 AS c15,
                                    C24 AS c16,
                                    C26 AS c17,
                                    C2 AS c18,
                                    C28 AS c19
                                FROM REPORT3
                               
                            """)
                
                result = dictfetchall(cursor)
                
            return Response({'success': True, 'result': result })
        except:
            return Response({'success': False})
        
        
class Reportall(APIView):
    
     def get(self, request, format = None):
        try:
            with connection.cursor() as cursor:
                
                cursor.execute("""
                               
                            with rep as
                            (
                            select R1.MODIFIEDSOL, trunc(R1.DATECREATED) as createddate,max(5) as document_id, count(*)  as rep_cnt from report1 r1
                            group by R1.MODIFIEDSOL, trunc(R1.DATECREATED)
                            union all
                            select modified_sol, created_date, 20 as DOC_TYPE_ID, count(*) from 
                            (
                                select to_char(C23) as modified_sol,trunc(C28) as created_date  from BTG_HHHA.REPORT3
                                union all
                                select to_char(C4),trunc(C3) from BTG_HHHA.REPORT2
                            ) group by modified_sol, created_date
                            ),
                            doc as
                            (
                                select  SOL.SOL_ID, trunc(SOL.UPLOADED_DATE) as created_date , sol.DOC_TYPE_ID as document_id,count(SOL.DOC_TYPE_ID ) as doc_cnt  from sol_document sol
                                where PRED_ID in ('22','29')
                                group by SOL.SOL_ID,trunc(SOL.UPLOADED_DATE), sol.DOC_TYPE_ID
                            )
                            select  MODIFIEDSOL, createddate, DOC_TYPE.DOC_TYPE_NAME, rep_cnt, DOC_CNT from rep 
                            left join doc on rep.MODIFIEDSOL= doc.SOL_ID and doc.created_date= rep.createddate and doc.document_id=rep.document_id
                            left join BTG_HHHA.DOCUMENT_TYPE doc_type  on DOC_TYPE.ID= doc.document_id
                            where doc_type.PRED_ID in ('22','29')
                            """)
                
                result = dictfetchall(cursor)
                
            return Response({'success': True, 'result': result })
        except:
            return Response({'success': False})
