import aioboto3
import aioboto3.session
from botocore.exceptions import ClientError
import logging
import asyncio

from extracttext import extract_text_from_pdf
from s3_operations import get_s3_object
from cvprocess import cvprocess
from cloudwatch_operations import log_to_cloudwatch_logs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ids = [
    'cm04852qe0000gvdq5i8h49p4',
    'cm048b0q8000054zr5rcu3ld4',
    'cm048pcsg0000126po89kt4b3',
    'cm048ytoq0005126pgxu15zjn',
    'cm0498caq000a126pum0t3351',
    'cm049fyt2000f126pyjb6ck0v',
    'cm049i47l000k126pu042hflz',
    'cm049pr4b000p126pgzo4tvkd',
    'cm04a8s6b0000ggv279l1asgk',
    'cm04abj9n0005ggv2smkew0tr',
    'cm04ajxw1000aggv2gabglv1j',
    'cm04b58hz000fggv2kccc2tcf',
    'cm04bd5sa000kggv2edn3n2ue',
    'cm04bncg10000wyw24equb5q5',
    'cm04byaay0005wyw232kkwfgn',
    'cm04chmh2000awyw29wiv9ll5',
    'cm04cn74h000fwyw2f6ho0rq6',
    'cm04denxc000kwyw2r7g1h0pe',
    'cm04dhygc000pwyw2dd88oufd',
    'cm04dtsuj0000vdxhdvqcezil',
    'cm04dx1rw0005vdxhrxroqtbs',
    'cm04e2nyk000avdxhwttq3toq',
    'cm04efbsu00002h69dp2jfk2e',
    'cm04enbgd00052h691enmcdkf',
    'cm04h9az500002ixfz7vjhq6o',
    'cm04k18540000w54eqsgmyefe',
    'cm04mcc5u0000janc1o7vbu0d',
    'cm04n04fa0000t5rwn1zszksc',
    'cm04pqv1g0000tdd4a4wmdr3y',
    'cm04qo2hn00052jz2i6a3iix2',
    'cm04qp0qq000a2jz2y6qitene',
    'cm04ruv4s00005dp9oe0j6wts',
    'cm04sd33400055dp9cvdiuwjx',
    'cm04sh2su000a5dp9303kmxhj',
    'cm04swm8q000010ir8herb5ul',
    'cm04t3s72000510ir7extsk11',
    'cm04t4o80000a10irldp2sjqs',
    'cm04t6jqs000f10irfhl79djs',
    'cm04t7o56000k10irs0y3s1k0',
    'cm04tinvg000p10ir9zls5d5d',
    'cm04tqa9v000u10ir4q79fhmd',
    'cm04u1svb000014htdnenut18',
    'cm04u5dxj000514ht5dsmqe1j',
    'cm04ukuve000a14ht23z0qdfn',
    'cm04uoz25000f14htdfu7dhwj',
    'cm04uy30v000k14htc1h33tez',
    'cm04vbkf00000uxjej2afi4fw',
    'cm04vmntv000013qru1jud43s',
    'cm04w8dxe000513qr7ohvgv5v',
    'cm04w8z4j000a13qr02ia9c9p',
    'cm04wwx70000010h08v27t59y',
    'cm04wxqz3000510h0nghdsi5o',
    'cm04x1fdj000a10h02clm596b',
    'cm04ynklr0000tdlfj53wb2g9',
    'cm04yrhgv0005tdlf10t1iix7',
    'cm04yvmf4000atdlf8xvppby5',
    'cm04zdaem000011duobhoudiv',
    'cm050ddax0000sv621kmswi4n',
    'cm051f4ke00007tht7czpxlfo',
    'cm0523dhf0000jcpnudbyoxy4',
    'cm055iqy800008y1nzzdz8686',
    'cm055n1gq00005557zjyvl26w',
    'cm0570chm000013tateejfbmp',
    'cm057hebd00003v147ypz4gxz',
    'cm057ls5900053v14ponr1fav',
    'cm058qppt00009bmiabftbxco',
    'cm059rq620000ehn4orzupgtt',
    'cm05afnc20000acq712huhy22',
    'cm05ah4420005acq727ih0dhk',
    'cm05dvg6o0000s2oqlzcklejx',
    'cm05i5r0j0000oithmijnm3wr',
    'cm05j9w0u0000dxmdjqaj5b4j',
    'cm05k4whg0000r0f1iis8tnni',
    'cm05pxlgv0000cooixruk6p7w',
    'cm071mal10000bd79kfchyckp',
    'cm080umji00007a5t1vyhx6r6',
    'cm08748f10000hxpkbzxsde90',
    'cm08ghais00005v5tzi2dh2fr',
    'cm09dvqva0000w3ijv1lf3m7m',
    'cm09sa4s400009907ho0eij6m',
    'cm0a3ctet0000jwvrmwy5wf5v',
    'cm0agimop0000pgjsj6o2o7mf'
]

SPECIFIC_KEYS = [f'resumes/{id}/resume.pdf' for id in ids]

BUCKET_NAME = 'wynt'
LOG_STREAM_NAME = 's3_processing_stream'

async def process_specific_s3_objects():
    session = aioboto3.Session()  # Create an async session
    async with session.client ('s3') as s3:
        for key in SPECIFIC_KEYS:
            try:
                logger.info(f"Processing specific file: s3://{BUCKET_NAME}/{key}")
                await log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Processing file: s3://{BUCKET_NAME}/{key}")

                # Assuming get_s3_object is async
                file_content, metadata = await get_s3_object(s3, BUCKET_NAME, key)

                # Run extract_text_from_pdf in a separate thread since it is likely not async
                extracted_text = await asyncio.to_thread(extract_text_from_pdf, file_content)

                logger.info(f"Extracted text from {key}: {extracted_text[:100]}...")

                await cvprocess(metadata, extracted_text)

                await log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Finished processing file: {key} successfully.")

            except ClientError as e:
                logger.error(f"Error processing file {key}: {str(e)}")
                await log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Client error occurred while processing file: {key}.")
            except Exception as e:
                logger.error(f"Unexpected error during processing file {key}: {str(e)}")
                await log_to_cloudwatch_logs(LOG_STREAM_NAME, f"Unexpected error occurred while processing file: {key}.")
