# QUICK START GUIDE
## Complete Deployment in 8 Days

---

## ⚡ STEP-BY-STEP EXECUTION

### **DAY 1 (Feb 2): Prepare & Test Locally**

```bash
# 1. Prepare your model
python step1_model_preparation.py

# 2. Test API locally
python step2_api_service.py
# API will run on http://localhost:5000

# 3. In another terminal, test the API
curl http://localhost:5000/health
curl http://localhost:5000/api/v1/recommendations/user/1?n=10

# 4. Build Docker container
docker build -t recommendation-api .

# 5. Test with Docker Compose
docker-compose up
# Visit http://localhost:5000/health
```

**Verification:**
- ✓ Model loads successfully
- ✓ API returns recommendations
- ✓ Docker container runs

---

### **DAY 2 (Feb 3): Deploy to Cloud**

```bash
# AWS Deployment
python step4_cloud_deployment_aws.py

# Or use manual commands:

# 1. Create ECR repository
aws ecr create-repository --repository-name recommendation-api

# 2. Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# 3. Tag and push image
docker tag recommendation-api:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/recommendation-api:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/recommendation-api:latest

# 4. Create ECS cluster
aws ecs create-cluster --cluster-name recommendation-cluster

# 5. Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 6. Create service
aws ecs create-service \
  --cluster recommendation-cluster \
  --service-name recommendation-service \
  --task-definition recommendation-task \
  --desired-count 2 \
  --launch-type FARGATE
```

**Verification:**
- ✓ Image in container registry
- ✓ ECS cluster running
- ✓ API accessible from cloud URL

---

### **DAY 3 (Feb 4): Monitoring & Performance**

```bash
# 1. Run performance tests
python step6_performance_testing.py

# 2. Check metrics
curl http://YOUR_API_URL/metrics
curl http://YOUR_API_URL/health

# 3. View logs (AWS)
aws logs tail /ecs/recommendation-api --follow
```

**Verification:**
- ✓ Response time < 200ms
- ✓ Monitoring dashboards working
- ✓ Alerts configured

---

### **DAY 4 (Feb 5-6): Frontend Integration**

```html
<!-- Add to your HTML -->
<link rel="stylesheet" href="step5_recommendations_styles.css">
<script src="step5_frontend_integration.js"></script>

<!-- Homepage -->
<div id="homepage-recommendations"></div>
<script>
  loadHomepageRecommendations();
</script>

<!-- Product Page -->
<div id="similar-products"></div>
<script>
  const productId = 123; // Current product
  loadSimilarProducts(productId);
</script>

<!-- User Dashboard -->
<div id="recommended-for-you"></div>
<script>
  const userId = getCurrentUserId();
  loadPersonalizedRecommendations(userId);
</script>
```

**Verification:**
- ✓ Recommendations appear on all pages
- ✓ Styling looks good
- ✓ Click tracking working

---

### **DAY 5 (Feb 7-8): Testing**

```bash
# Full integration test
python step6_performance_testing.py

# Check specific endpoints
curl http://YOUR_API_URL/api/v1/recommendations/user/1?n=10
curl http://YOUR_API_URL/api/v1/recommendations/similar/5?n=8
curl http://YOUR_API_URL/api/v1/recommendations/popular?n=12
```

**Verification:**
- ✓ All user flows working
- ✓ Load tests passing
- ✓ No critical bugs

---

### **DAY 6 (Feb 9): Final Validation**

```bash
# Run checklist
python step8_deployment_checklist.py

# Final performance test
python step6_performance_testing.py

# Verify success criteria
# - Response time < 200ms ✓
# - Uptime >= 99.5% ✓
# - Real-time suggestions ✓
```

---

### **DAY 7 (Feb 10): GO LIVE! 🚀**

**Morning (10:00 AM):**
```bash
# Start with 10% traffic
aws ecs update-service \
  --cluster recommendation-cluster \
  --service recommendation-service \
  --desired-count 1

# Monitor for 1 hour
watch -n 10 'curl http://YOUR_API_URL/health'
```

**Midday (11:30 AM):**
```bash
# Increase to 50% traffic
aws ecs update-service \
  --cluster recommendation-cluster \
  --service recommendation-service \
  --desired-count 5

# Continue monitoring
```

**Afternoon (1:00 PM):**
```bash
# Full deployment - 100% traffic
aws ecs update-service \
  --cluster recommendation-cluster \
  --service recommendation-service \
  --desired-count 10

# Monitor continuously
```

---

## 🔧 TROUBLESHOOTING

### Issue: API not responding
```bash
# Check service status
aws ecs describe-services --cluster recommendation-cluster --services recommendation-service

# Check container logs
aws logs tail /ecs/recommendation-api --follow

# Restart service
aws ecs update-service --cluster recommendation-cluster --service recommendation-service --force-new-deployment
```

### Issue: High latency
```bash
# Check Redis cache
redis-cli ping

# Increase container resources
# Update task definition with more CPU/memory

# Scale up instances
aws ecs update-service --cluster recommendation-cluster --service recommendation-service --desired-count 5
```

### Issue: Recommendations not showing
```javascript
// Check browser console for errors
console.log('API URL:', recoClient.apiBaseUrl);

// Test API directly
fetch('http://YOUR_API_URL/api/v1/recommendations/user/1?n=10')
  .then(r => r.json())
  .then(data => console.log(data));

// Check CORS headers
```

---

## 📊 KEY METRICS TO MONITOR

**Performance Metrics:**
- Response Time: < 200ms (95th percentile)
- Throughput: > 100 req/sec
- Error Rate: < 1%
- Cache Hit Rate: > 50%

**Business Metrics:**
- Click-Through Rate: > 2%
- Conversion Rate: Track improvement
- Average Order Value: Track improvement

**System Metrics:**
- CPU Usage: < 80%
- Memory Usage: < 80%
- Uptime: > 99.5%

---

## 🎯 SUCCESS CRITERIA CHECKLIST

By Feb 10, you should have:

✓ Recommendation API deployed to production
✓ Integration complete on all pages
✓ Response time < 200ms (95th percentile)
✓ System runs reliably (99.5%+ uptime)
✓ Real-time product suggestions working
✓ Monitoring and alerts configured
✓ Documentation complete
✓ Team trained on rollback procedure

---

## 📞 SUPPORT

If you encounter issues:
1. Check logs: `aws logs tail /ecs/recommendation-api`
2. Review monitoring dashboard
3. Check deployment checklist: `python step8_deployment_checklist.py`
4. Review rollback procedure if needed

---

## 🎉 POST-LAUNCH

After successful deployment:
1. Monitor performance for 24 hours
2. Gather user feedback
3. Track business metrics (CTR, conversions)
4. Plan optimizations based on data
5. Document lessons learned

**Congratulations on completing Milestone 4!** 🚀
