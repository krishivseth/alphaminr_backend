@app.route('/api/cron/generate', methods=['POST'])
def cron_generate():
    """Cron job endpoint for automated newsletter generation"""
    # Verify this is a legitimate cron request
    cron_secret = os.environ.get('CRON_SECRET')
    if not cron_secret:
        logger.warning("⚠️ CRON_SECRET not set - allowing all requests")
    else:
        provided_secret = request.headers.get('X-Cron-Secret')
        if provided_secret != cron_secret:
            logger.error("❌ Invalid cron secret")
            return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    logger.info("🕐 Cron job triggered newsletter generation")
    
    # Call the existing generation logic
    start_time = datetime.now()
    
    try:
        # Check environment variables
        if not BRAVE_SEARCH_API_KEY or not ANTHROPIC_API_KEY:
            error_msg = "Missing required environment variables"
            logger.error(f"❌ {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 500
        
        # Generate newsletter
        generation_start = datetime.now()
        logger.info(f"⚡ Starting cron newsletter generation at {generation_start}")
        
        html_output = generate_newsletter_content()
        
        if not html_output:
            logger.error("❌ Failed to generate content")
            return jsonify({"success": False, "error": "Failed to generate content"}), 500
        
        # Generate unique ID for this newsletter
        newsletter_id = str(uuid.uuid4())
        
        # Initialize database and save newsletter
        init_database()
        save_newsletter_to_db(newsletter_id, html_output)
        
        generation_end = datetime.now()
        generation_duration = (generation_end - generation_start).total_seconds()
        total_duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Cron newsletter generated successfully in {generation_duration:.2f}s")
        
        return jsonify({
            "success": True,
            "newsletter_id": newsletter_id,
            "generation_time_seconds": generation_duration,
            "total_time_seconds": total_duration,
            "message": "Cron newsletter generated successfully"
        })
        
    except Exception as e:
        logger.error(f"❌ Cron newsletter generation failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
