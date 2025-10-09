# Custom Domain Setup Guide: headshot-creator.databooth.com.au

This guide walks you through setting up a custom domain for your Headshots app on Render using your existing `databooth.com.au` domain.

## 🎯 Goal
Transform `https://headshots-sdqf.onrender.com` → `https://headshot-creator.databooth.com.au`

## 📋 Prerequisites
- ✅ You own `databooth.com.au` domain
- ✅ Access to your domain's DNS management (where you manage DNS records)
- ✅ Render service is deployed and working (`srv-d3j0lnbe5dus739f5bi0`)

## 🚀 Step-by-Step Setup

### Step 1: Add Custom Domain in Render Dashboard

1. **Go to your service dashboard:**
   - Navigate to: https://dashboard.render.com/web/srv-d3j0lnbe5dus739f5bi0
   - Or find "Headshots" service in your Render dashboard

2. **Add custom domain:**
   - Click on "Settings" tab
   - Scroll to "Custom Domains" section
   - Click "Add Custom Domain"
   - Enter: `headshot-creator.databooth.com.au`
   - Click "Save"

3. **Note the CNAME record details:**
   - Render will provide you with a CNAME target (something like `headshots-sdqf.onrender.com`)
   - Keep this information handy for Step 2

### Step 2: Configure DNS Records

You'll need to add a CNAME record in your DNS management system. Here are instructions for common providers:

#### Option A: If you use Cloudflare for DNS
1. Log into Cloudflare dashboard
2. Select your `databooth.com.au` domain
3. Go to "DNS" → "Records"
4. Click "Add record"
5. Configure:
   - **Type:** CNAME
   - **Name:** `headshot-creator`
   - **Content:** `headshots-sdqf.onrender.com` (from Render dashboard)
   - **Proxy status:** 🟢 Proxied (recommended) or ☁️ DNS only
   - **TTL:** Auto
6. Click "Save"

#### Option B: If you use your registrar's DNS (e.g., GoDaddy, Namecheap)
1. Log into your domain registrar account
2. Find DNS management for `databooth.com.au`
3. Add new DNS record:
   - **Type:** CNAME
   - **Host/Name:** `headshot-creator`
   - **Points to/Value:** `headshots-sdqf.onrender.com`
   - **TTL:** 300 (or default)
4. Save changes

#### Option C: If you use Route 53 (AWS)
1. Go to AWS Route 53 console
2. Select your `databooth.com.au` hosted zone
3. Click "Create record"
4. Configure:
   - **Record name:** `headshot-creator`
   - **Record type:** CNAME
   - **Value:** `headshots-sdqf.onrender.com`
   - **TTL:** 300
5. Click "Create records"

### Step 3: Enable HTTPS/SSL

1. **In Render dashboard:**
   - Go back to your service settings
   - Find "Custom Domains" section
   - Your domain should show "Certificate Pending" or similar
   - Wait 5-15 minutes for automatic SSL certificate provisioning

2. **Render automatically provides:**
   - Free SSL/TLS certificate via Let's Encrypt
   - Automatic HTTPS redirect
   - Certificate auto-renewal

### Step 4: Verification & Testing

1. **Wait for DNS propagation** (5 minutes to 24 hours, usually < 1 hour)

2. **Test DNS resolution:**
   ```bash
   # Check if CNAME is resolving
   nslookup headshot-creator.databooth.com.au
   
   # Should show something like:
   # headshot-creator.databooth.com.au canonical name = headshots-sdqf.onrender.com
   ```

3. **Test the website:**
   - Visit: `https://headshot-creator.databooth.com.au`
   - Should load your Headshot Creator app
   - SSL certificate should be valid (green lock icon)

4. **Check redirects:**
   - HTTP should auto-redirect to HTTPS
   - Old URL still works: `https://headshots-sdqf.onrender.com`

## 🔧 Troubleshooting

### Common Issues:

#### "SSL Certificate Pending" (15+ minutes)
- **Cause:** DNS not fully propagated or misconfigured CNAME
- **Solution:** 
  - Verify CNAME record is correct
  - Wait longer (up to 24 hours for DNS)
  - Check for typos in domain name

#### "Domain Not Found" Error
- **Cause:** DNS record not configured or propagated
- **Solution:**
  - Double-check CNAME record points to correct Render URL
  - Try different DNS checker: https://whatsmydns.net/

#### Mixed Content Warnings
- **Cause:** Some assets loading over HTTP instead of HTTPS
- **Solution:** Usually resolves automatically; contact Render support if persistent

### DNS Propagation Check Tools:
- https://whatsmydns.net/ (check global propagation)
- https://dnschecker.org/ (multiple location check)

## 📊 Expected Timeline

| Step | Time Required |
|------|---------------|
| Add domain in Render | 2 minutes |
| Configure DNS record | 5 minutes |
| DNS propagation | 5 minutes - 24 hours |
| SSL certificate | 5-15 minutes |
| **Total** | **15 minutes - 24 hours** |

*Most setups complete within 1 hour*

## 🎉 Success Checklist

- [ ] Domain added in Render dashboard
- [ ] CNAME record configured in DNS
- [ ] `nslookup` shows correct resolution
- [ ] Website loads at `https://headshot-creator.databooth.com.au`
- [ ] SSL certificate is valid (green lock)
- [ ] HTTP redirects to HTTPS automatically

## 🔄 Post-Setup (Optional)

### Update Your Marketing Materials
- Update any documentation to reference new URL
- Consider adding a redirect from old URL (if you want to phase it out)

### Configure Additional Domains (Optional)
You could also add:
- `headshots.databooth.com.au` (shorter alternative)
- `headshot.databooth.com.au` (without hyphen)

Just repeat the process with different subdomain names.

## 🆘 Need Help?

1. **DNS Issues:** Contact your DNS provider support
2. **Render Issues:** https://render.com/support
3. **SSL Issues:** Usually resolve automatically; wait 24 hours before contacting support

## 🔗 Useful Links

- [Render Custom Domains Documentation](https://render.com/docs/custom-domains)
- [DNS Propagation Checker](https://whatsmydns.net/)
- [SSL Certificate Checker](https://www.ssllabs.com/ssltest/)

---

**✨ Result:** Professional URL that matches your DataBooth branding and builds trust with users!