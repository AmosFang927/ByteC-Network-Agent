#!/usr/bin/env python3
"""
Postback-Agent Main Application
Simple FastAPI application for handling postback data
"""

import os
import sys
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Optional, Dict, Any
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for health checks
startup_time = None
health_status = {"status": "healthy", "service": "postback-agent"}
postback_records = []
record_counter = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global startup_time
    startup_time = datetime.now()
    logger.info("🚀 Postback-Agent 启动中...")
    
    try:
        # Initialize any database connections or other resources here
        logger.info("✅ Postback-Agent 启动成功")
        yield
    except Exception as e:
        logger.error(f"❌ Postback-Agent 启动失败: {e}")
        raise
    finally:
        logger.info("🔄 Postback-Agent 关闭中...")

def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="Postback-Agent API",
        description="ByteC Network Agent - Postback Data Processing System",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "Postback-Agent API",
            "version": "1.0.0",
            "description": "ByteC Network Agent - Postback Data Processing System",
            "status": "running",
            "endpoints": [
                "/involve/event",
                "/postback/",
                "/health",
                "/stats"
            ]
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "postback-agent",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "total_records": len(postback_records)
        }
    
    @app.get("/liveness")
    async def liveness_probe():
        """Kubernetes liveness probe"""
        return {"status": "alive"}
    
    @app.get("/readiness")
    async def readiness_probe():
        """Kubernetes readiness probe"""
        return {"status": "ready"}
    
    # Postback endpoints
    @app.get("/involve/event")
    async def involve_postback_get(
        request: Request,
        sub_id: Optional[str] = Query(None, description="发布商参数1 (aff_sub)"),
        media_id: Optional[str] = Query(None, description="媒体ID (aff_sub2)"),
        click_id: Optional[str] = Query(None, description="点击ID (aff_sub3)"),
        usd_sale_amount: Optional[str] = Query(None, description="美元销售金额"),
        usd_payout: Optional[str] = Query(None, description="美元佣金"),
        offer_name: Optional[str] = Query(None, description="Offer名称"),
        conversion_id: Optional[str] = Query(None, description="转换ID"),
        conversion_datetime: Optional[str] = Query(None, description="转换时间"),
        offer_id: Optional[str] = Query(None, description="Offer ID"),
        order_id: Optional[str] = Query(None, description="订单ID"),
        status: Optional[str] = Query(None, description="状态"),
    ):
        """ByteC Involve Asia Postback endpoint"""
        global record_counter
        start_time = time.time()
        
        try:
            record_counter += 1
            
            # Process the postback data
            processed_data = {
                "conversion_id": conversion_id,
                "offer_id": offer_id,
                "offer_name": offer_name,
                "conversion_datetime": conversion_datetime,
                "order_id": order_id,
                "sub_id": sub_id,
                "media_id": media_id,
                "click_id": click_id,
                "usd_sale_amount": usd_sale_amount,
                "usd_payout": usd_payout,
                "status": status,
                "raw_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
            
            # Store the record
            record = {
                "id": record_counter,
                "timestamp": time.time(),
                "method": "GET",
                "endpoint": "/involve/event",
                "data": processed_data,
                "processing_time_ms": (time.time() - start_time) * 1000
            }
            
            postback_records.append(record)
            
            logger.info(f"✅ Involve postback processed: conversion_id={conversion_id}, "
                       f"click_id={click_id}, time={record['processing_time_ms']:.2f}ms")
            
            return JSONResponse({
                "status": "success",
                "method": "GET",
                "endpoint": "/involve/event",
                "data": processed_data,
                "record_id": record_counter,
                "message": "Postback received successfully"
            })
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Involve postback error: {str(e)}, time={processing_time:.2f}ms")
            return JSONResponse({
                "status": "error",
                "method": "GET",
                "endpoint": "/involve/event",
                "error": str(e),
                "message": "Postback processing failed"
            }, status_code=500)
    
    @app.post("/involve/event")
    async def involve_postback_post(
        request: Request,
        sub_id: Optional[str] = Query(None, description="发布商参数1 (aff_sub)"),
        media_id: Optional[str] = Query(None, description="媒体ID (aff_sub2)"),
        click_id: Optional[str] = Query(None, description="点击ID (aff_sub3)"),
        usd_sale_amount: Optional[str] = Query(None, description="美元销售金额"),
        usd_payout: Optional[str] = Query(None, description="美元佣金"),
        offer_name: Optional[str] = Query(None, description="Offer名称"),
        conversion_id: Optional[str] = Query(None, description="转换ID"),
        conversion_datetime: Optional[str] = Query(None, description="转换时间"),
    ):
        """ByteC Involve Asia Postback endpoint (POST)"""
        global record_counter
        start_time = time.time()
        
        try:
            record_counter += 1
            
            # Try to get body data
            body_data = {}
            try:
                body_data = await request.json()
            except:
                pass
            
            # Process the postback data
            processed_data = {
                "conversion_id": conversion_id,
                "offer_name": offer_name,
                "conversion_datetime": conversion_datetime,
                "sub_id": sub_id,
                "media_id": media_id,
                "click_id": click_id,
                "usd_sale_amount": usd_sale_amount,
                "usd_payout": usd_payout,
                "body_data": body_data,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else "unknown"
            }
            
            # Store the record
            record = {
                "id": record_counter,
                "timestamp": time.time(),
                "method": "POST",
                "endpoint": "/involve/event",
                "data": processed_data,
                "processing_time_ms": (time.time() - start_time) * 1000
            }
            
            postback_records.append(record)
            
            logger.info(f"✅ Involve postback (POST) processed: conversion_id={conversion_id}, "
                       f"time={record['processing_time_ms']:.2f}ms")
            
            return JSONResponse({
                "status": "success",
                "method": "POST",
                "endpoint": "/involve/event",
                "data": processed_data,
                "record_id": record_counter,
                "message": "Postback received successfully"
            })
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Involve postback (POST) error: {str(e)}, time={processing_time:.2f}ms")
            return JSONResponse({
                "status": "error",
                "method": "POST",
                "endpoint": "/involve/event",
                "error": str(e),
                "message": "Postback processing failed"
            }, status_code=500)
    
    @app.get("/postback/")
    async def postback_get(
        request: Request,
        conversion_id: str = Query(..., description="转换ID"),
        offer_id: Optional[str] = Query(None, description="Offer ID"),
        offer_name: Optional[str] = Query(None, description="Offer名称"),
        usd_sale_amount: Optional[float] = Query(None, description="美元销售金额"),
        usd_payout: Optional[float] = Query(None, description="美元佣金"),
        aff_sub: Optional[str] = Query(None, description="发布商参数1"),
        aff_sub2: Optional[str] = Query(None, description="发布商参数2"),
        aff_sub3: Optional[str] = Query(None, description="发布商参数3"),
        status: Optional[str] = Query(None, description="状态"),
    ):
        """Generic postback endpoint"""
        global record_counter
        start_time = time.time()
        
        try:
            record_counter += 1
            
            processed_data = {
                "conversion_id": conversion_id,
                "offer_id": offer_id,
                "offer_name": offer_name,
                "usd_sale_amount": usd_sale_amount,
                "usd_payout": usd_payout,
                "aff_sub": aff_sub,
                "aff_sub2": aff_sub2,
                "aff_sub3": aff_sub3,
                "status": status,
                "raw_params": dict(request.query_params)
            }
            
            record = {
                "id": record_counter,
                "timestamp": time.time(),
                "method": "GET",
                "endpoint": "/postback/",
                "data": processed_data,
                "processing_time_ms": (time.time() - start_time) * 1000
            }
            
            postback_records.append(record)
            
            logger.info(f"✅ Generic postback processed: conversion_id={conversion_id}, "
                       f"time={record['processing_time_ms']:.2f}ms")
            
            return JSONResponse({
                "status": "success",
                "method": "GET",
                "endpoint": "/postback/",
                "data": processed_data,
                "record_id": record_counter,
                "message": "Postback received successfully"
            })
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"❌ Generic postback error: {str(e)}, time={processing_time:.2f}ms")
            return JSONResponse({
                "status": "error",
                "method": "GET",
                "endpoint": "/postback/",
                "error": str(e),
                "message": "Postback processing failed"
            }, status_code=500)
    
    @app.get("/stats")
    async def get_stats():
        """Get postback statistics"""
        return {
            "total_records": len(postback_records),
            "total_processed": record_counter,
            "recent_records": postback_records[-10:] if postback_records else [],
            "endpoints": {
                "involve_event": len([r for r in postback_records if r["endpoint"] == "/involve/event"]),
                "postback": len([r for r in postback_records if r["endpoint"] == "/postback/"]),
            }
        }
    
    @app.get("/records")
    async def get_records(limit: int = Query(10, description="返回记录数量")):
        """Get recent postback records"""
        return {
            "total_records": len(postback_records),
            "records": postback_records[-limit:] if postback_records else [],
            "message": f"Showing last {min(limit, len(postback_records))} records"
        }
    
    return app

# Create app instance
app = create_app()

def main():
    """Main function to run the application"""
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"🚀 启动 Postback-Agent")
    logger.info(f"📡 监听地址: http://{host}:{port}")
    logger.info(f"🏥 健康检查: http://{host}:{port}/health")
    logger.info(f"📊 统计信息: http://{host}:{port}/stats")
    logger.info(f"📖 API文档: http://{host}:{port}/docs")
    logger.info(f"🔄 Postback端点: http://{host}:{port}/involve/event")
    logger.info(f"🔄 通用端点: http://{host}:{port}/postback/")
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=False
        )
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 