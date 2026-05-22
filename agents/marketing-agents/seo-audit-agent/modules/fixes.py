"""
fixes.py — Step-by-step fix guides for every SEO issue type.
Each fix includes: steps, code example, difficulty, time estimate, and impact.
"""

FIX_GUIDES = {

    # ── META TAGS ──────────────────────────────────────────────────────────────

    "No <title> tag": {
        "title": "Add a Title Tag",
        "difficulty": "Easy",
        "time": "5 minutes",
        "impact": "High",
        "summary": "The title tag is the single most important on-page SEO element. It appears as the blue clickable headline in Google search results.",
        "steps": [
            "Open your page's HTML file or CMS template",
            "Find the <head> section (near the top of the file)",
            "Add a <title> tag inside <head> with your primary keyword near the front",
            "Keep it between 50–60 characters including spaces",
            "Save and publish the page",
            "Use Google Search Console to request re-indexing"
        ],
        "code": """<!-- Add inside your <head> section -->
<head>
  <title>Primary Keyword | Brand Name — Short Description</title>
</head>

<!-- Good examples: -->
<title>Buy Organic Coffee Beans Online | FreshRoast — Free UK Delivery</title>
<title>AI SEO Audit Tool — Free Website Analysis | AuditPro</title>
<title>Python Django Tutorial for Beginners | DevLearn 2024</title>""",
        "do": ["Put your primary keyword near the beginning", "Make it unique for every page", "Match the user's search intent"],
        "dont": ["Don't stuff multiple keywords", "Don't use the same title on every page", "Don't go over 60 characters"],
    },

    "Title too short": {
        "title": "Expand Your Title Tag",
        "difficulty": "Easy",
        "time": "5 minutes",
        "impact": "Medium",
        "summary": "Short titles waste valuable space in search results. Google shows up to 600px (about 60 characters). Expand to describe your page fully and improve click-through rate.",
        "steps": [
            "Identify your primary keyword for this page",
            "Write a title that includes: primary keyword + benefit/differentiator + brand name",
            "Use a separator (|, —, :) between sections",
            "Aim for 50–60 characters",
            "Test how it looks using a SERP simulator"
        ],
        "code": """<!-- Too short (wastes space): -->
<title>Coffee Beans</title>

<!-- Improved (50-60 chars, includes keyword + value): -->
<title>Premium Coffee Beans | Free Shipping | FreshRoast</title>
<title>Organic Colombian Coffee — Single Origin | RoastCo</title>""",
        "do": ["Include brand name at the end", "Add a unique value proposition", "Use your primary keyword naturally"],
        "dont": ["Don't pad with filler words just to hit the limit", "Don't sacrifice clarity for length"],
    },

    "Title too long": {
        "title": "Shorten Your Title Tag",
        "difficulty": "Easy",
        "time": "5 minutes",
        "impact": "Medium",
        "summary": "Google truncates titles over ~60 characters with '...' in search results, cutting off your message and potentially your brand name.",
        "steps": [
            "Count your current title characters",
            "Identify the least important words to remove",
            "Remove filler words: 'the', 'a', 'and', 'for', 'with'",
            "Drop secondary keywords — keep only the primary one",
            "Move brand name to the end if it's taking space at the front",
            "Verify it's under 60 characters"
        ],
        "code": """<!-- Too long (74 chars — gets cut off): -->
<title>Buy Fresh Organic Colombian Single-Origin Coffee Beans Online with Free Delivery</title>

<!-- Fixed (55 chars — displays fully): -->
<title>Organic Colombian Coffee Beans — Free Delivery | RoastCo</title>""",
        "do": ["Keep the primary keyword", "Preserve the brand name", "Use active, punchy language"],
        "dont": ["Don't remove the primary keyword to save space", "Don't use ellipsis yourself"],
    },

    "No meta description": {
        "title": "Add a Meta Description",
        "difficulty": "Easy",
        "time": "10 minutes",
        "impact": "High",
        "summary": "The meta description is the gray text under your title in Google. It doesn't directly affect rankings, but a compelling description significantly improves click-through rate — which does affect rankings.",
        "steps": [
            "Open your page's HTML or CMS settings",
            "Find the meta description field (in CMS) or <head> section (in HTML)",
            "Write a description that summarises the page in 150–160 characters",
            "Include your primary keyword naturally",
            "Add a call-to-action (Learn more, Get started, Shop now)",
            "Make it unique — different from every other page on your site"
        ],
        "code": """<!-- Add inside your <head> section -->
<head>
  <meta name="description" content="Your compelling 150-160 character description here. Include primary keyword and a clear call to action for users.">
</head>

<!-- Real examples: -->
<meta name="description"
  content="Shop premium organic coffee beans from Colombia & Ethiopia. Free UK delivery on orders over £25. Fresh roasted weekly — order by Thursday for Friday delivery.">

<meta name="description"
  content="Free AI-powered SEO audit in 60 seconds. Analyse meta tags, keywords, technical issues & get GPT-4o recommendations. No signup required.">""",
        "do": ["Include your primary keyword", "Add a clear CTA", "Make every page's description unique"],
        "dont": ["Don't copy the title tag", "Don't stuff keywords", "Don't go over 160 characters"],
    },

    "Meta description too short": {
        "title": "Expand Your Meta Description",
        "difficulty": "Easy",
        "time": "10 minutes",
        "impact": "Medium",
        "summary": "Short descriptions leave valuable SERP space unused. Use the full 150–160 characters to sell your page and improve click-through rate.",
        "steps": [
            "Review your current meta description",
            "Identify what value you're not communicating",
            "Add: what the page is about + who it's for + why to click",
            "Include a call-to-action verb",
            "Check character count is between 150–160"
        ],
        "code": """<!-- Too short: -->
<meta name="description" content="Buy coffee beans online.">

<!-- Expanded (158 chars): -->
<meta name="description"
  content="Shop 20+ varieties of fresh roasted organic coffee beans. Single-origin Colombia, Ethiopia & Brazil. Free delivery over £25. Roasted to order weekly.">""",
        "do": ["Use the full space", "Include social proof if possible", "Use active verbs"],
        "dont": ["Don't pad with meaningless words", "Don't repeat the same phrase twice"],
    },

    "Meta description too long": {
        "title": "Shorten Your Meta Description",
        "difficulty": "Easy",
        "time": "5 minutes",
        "impact": "Low",
        "summary": "Google truncates descriptions over ~160 characters, cutting your message mid-sentence. Trim to ensure your full call-to-action is visible.",
        "steps": [
            "Count your current description characters",
            "Identify the least critical information",
            "Remove duplicate information already in the title",
            "Tighten sentences — replace 'in order to' with 'to'",
            "End with a clear CTA within 160 chars"
        ],
        "code": """<!-- Too long (gets cut with '...'): -->
<meta name="description"
  content="We offer a wide range of premium organic coffee beans sourced directly from farms in Colombia, Ethiopia, Brazil, and Guatemala. Free delivery on all orders over £25 with same-day dispatch.">

<!-- Fixed (156 chars): -->
<meta name="description"
  content="Premium organic coffee from Colombia, Ethiopia & Brazil. Direct from the farm. Free delivery over £25. Same-day dispatch Monday–Friday.">""",
        "do": ["End with a CTA", "Use em-dashes to save space", "Test in a SERP preview tool"],
        "dont": ["Don't cut mid-sentence", "Don't remove the primary keyword"],
    },

    "No canonical URL": {
        "title": "Add a Canonical Tag",
        "difficulty": "Easy",
        "time": "10 minutes",
        "impact": "Medium",
        "summary": "The canonical tag tells Google which version of a page is the 'master' copy. Without it, Google may index duplicate pages (http vs https, www vs non-www, trailing slash vs no slash) and split your PageRank.",
        "steps": [
            "Decide the canonical (preferred) URL for this page",
            "Always use the full absolute URL including https://",
            "Add the canonical link tag in the <head> section",
            "If using a CMS (WordPress, Shopify, Webflow), use the SEO plugin's canonical field",
            "Ensure all variations of the URL redirect to the canonical version"
        ],
        "code": """<!-- Add inside <head> — always use absolute URL with https -->
<head>
  <link rel="canonical" href="https://www.yoursite.com/coffee-beans/">
</head>

<!-- WordPress (Yoast SEO plugin) — set in page settings -->
<!-- Shopify — set in theme.liquid or page template -->
<!-- Webflow — set in page SEO settings -->

<!-- If you have pagination, use rel="next" and rel="prev" -->
<link rel="canonical" href="https://www.yoursite.com/blog/">
<link rel="next" href="https://www.yoursite.com/blog/page/2/">""",
        "do": ["Use absolute URLs (not relative)", "Self-reference every page", "Match the canonical to your preferred domain format"],
        "dont": ["Don't point canonicals at 404 pages", "Don't use canonicals as a redirect substitute"],
    },

    "No viewport meta tag": {
        "title": "Add a Viewport Meta Tag",
        "difficulty": "Easy",
        "time": "5 minutes",
        "impact": "High",
        "summary": "Without a viewport tag, mobile devices render your page at desktop width and scale it down — making text tiny and unreadable. Google uses mobile-first indexing, so this directly impacts rankings.",
        "steps": [
            "Open your HTML template or CMS theme file",
            "Find the <head> section",
            "Add the standard viewport meta tag",
            "Save and test on a mobile device or Chrome DevTools"
        ],
        "code": """<!-- Add this EXACT tag inside <head> — don't modify it -->
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>

<!-- For apps with zoom disabled (use cautiously): -->
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">

<!-- Verify in Chrome DevTools:
     1. Press F12 → Toggle Device Toolbar (Ctrl+Shift+M)
     2. Select a mobile device
     3. Page should display correctly without horizontal scroll -->""",
        "do": ["Use the standard tag exactly as shown", "Test on multiple screen sizes", "Ensure text is readable without zooming"],
        "dont": ["Don't disable user-scaling without good reason", "Don't use fixed pixel widths in CSS"],
    },

    "Page is NOINDEX": {
        "title": "Remove NOINDEX from Robots Meta Tag",
        "difficulty": "Medium",
        "time": "15 minutes",
        "impact": "Critical",
        "summary": "This page is telling Google NOT to include it in search results. This is the most severe SEO issue possible — the page is completely invisible to search engines.",
        "steps": [
            "Identify where the noindex instruction comes from (meta tag or HTTP header)",
            "Check your CMS settings — many have a 'discourage search engines' checkbox",
            "Remove 'noindex' from the robots meta tag in your HTML",
            "If using WordPress: Settings → Reading → uncheck 'Discourage search engines'",
            "Wait for Google to re-crawl (can take days to weeks)",
            "Use Google Search Console URL Inspection to request re-indexing"
        ],
        "code": """<!-- REMOVE this from your <head>: -->
<meta name="robots" content="noindex">
<meta name="robots" content="noindex, nofollow">

<!-- REPLACE with (allows indexing + following links): -->
<meta name="robots" content="index, follow">

<!-- Or just remove the robots meta tag entirely -->
<!-- (default behaviour is index + follow) -->

<!-- Check for HTTP header version too:
     X-Robots-Tag: noindex  ← must be removed from server config -->""",
        "do": ["Double-check in Google Search Console after fixing", "Request re-indexing via URL Inspection tool", "Also check X-Robots-Tag HTTP headers"],
        "dont": ["Don't add noindex to pages you want ranked", "Don't confuse noindex (this) with nofollow (links)"],
    },

    "Missing Open Graph tags": {
        "title": "Add Open Graph Meta Tags",
        "difficulty": "Easy",
        "time": "15 minutes",
        "impact": "Medium",
        "summary": "Open Graph tags control how your page appears when shared on Facebook, LinkedIn, and other platforms. Without them, social shares show wrong images, titles, or no preview at all.",
        "steps": [
            "Add the four essential OG tags to your <head> section",
            "Create a social sharing image: 1200×630px, under 1MB",
            "Upload the image and get its absolute URL",
            "Set og:title to your page title (can be slightly different from <title>)",
            "Set og:description to your meta description or a social-optimised version",
            "Test using Facebook Sharing Debugger: developers.facebook.com/tools/debug/"
        ],
        "code": """<!-- Add inside <head> — replace values with your actual content -->
<head>
  <!-- Essential OG tags -->
  <meta property="og:title" content="Your Page Title Here">
  <meta property="og:description" content="Your compelling 2-3 sentence description for social sharing.">
  <meta property="og:image" content="https://yoursite.com/images/og-cover.jpg">
  <meta property="og:url" content="https://yoursite.com/your-page/">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Your Brand Name">

  <!-- Twitter Card (separate system) -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Your Page Title Here">
  <meta name="twitter:description" content="Description for Twitter sharing.">
  <meta name="twitter:image" content="https://yoursite.com/images/og-cover.jpg">
</head>""",
        "do": ["Use 1200×630px images", "Make og:title compelling (can differ from <title>)", "Test with Facebook Debugger after adding"],
        "dont": ["Don't use images under 200×200px", "Don't set og:url to a different page", "Don't forget twitter:card type"],
    },

    # ── HEADINGS ───────────────────────────────────────────────────────────────

    "No H1 tag": {
        "title": "Add an H1 Heading",
        "difficulty": "Easy",
        "time": "5 minutes",
        "impact": "High",
        "summary": "The H1 is the main headline of your page. Google uses it to understand what the page is about. Every page must have exactly one H1 with the primary keyword.",
        "steps": [
            "Identify the primary keyword for this page",
            "Write a clear, descriptive H1 that contains that keyword",
            "Place the H1 near the top of your page content",
            "Ensure it's inside an <h1> HTML tag (not just styled text)",
            "Verify using browser DevTools: Ctrl+F → search for '<h1'"
        ],
        "code": """<!-- Add as the first heading in your page content -->
<h1>Primary Keyword — Page Topic</h1>

<!-- Good H1 examples: -->
<h1>Organic Colombian Coffee Beans — Fresh Roasted Weekly</h1>
<h1>Python Django Tutorial for Absolute Beginners (2024)</h1>
<h1>Free AI SEO Audit — Analyse Any Website in 60 Seconds</h1>

<!-- In WordPress: the Post/Page Title becomes H1 automatically -->
<!-- In Webflow: drag an H1 element to the top of your content -->
<!-- In HTML: always use <h1>, never fake it with CSS -->""",
        "do": ["Use your primary keyword naturally", "Make it descriptive and specific", "Match what users searching for this keyword would expect"],
        "dont": ["Don't use H1 more than once", "Don't make it a keyword list", "Don't use H2 or strong tags styled to look like H1"],
    },

    "Multiple H1 tags found": {
        "title": "Fix Multiple H1 Tags",
        "difficulty": "Medium",
        "time": "15 minutes",
        "impact": "Medium",
        "summary": "Having multiple H1 tags confuses search engines about which is the primary topic. Keep exactly one H1 and use H2–H6 for subheadings.",
        "steps": [
            "Use browser DevTools to find all H1 tags: F12 → Console → document.querySelectorAll('h1')",
            "Decide which H1 best represents the page's primary keyword",
            "Change all other H1 tags to H2 or H3 as appropriate",
            "Ensure your heading hierarchy makes logical sense: H1 → H2 → H3"
        ],
        "code": """<!-- BEFORE (multiple H1 — wrong): -->
<h1>Coffee Beans</h1>
<h1>Shop Our Collection</h1>  ← change this
<h1>Why Choose Us</h1>        ← change this

<!-- AFTER (one H1 + logical hierarchy): -->
<h1>Premium Coffee Beans — Organic & Fresh Roasted</h1>
<h2>Shop Our Collection</h2>
  <h3>Colombian Single-Origin</h3>
  <h3>Ethiopian Yirgacheffe</h3>
<h2>Why Choose FreshRoast</h2>

<!-- Check for hidden H1 tags in:
     - Navigation / logo links
     - Footer sections
     - Hidden/display:none elements (Google still reads them) -->""",
        "do": ["Keep exactly one H1 per page", "Use H2 for major sections", "Maintain logical nesting"],
        "dont": ["Don't have H3 without a preceding H2", "Don't use headings just for styling"],
    },

    "No H2 tags": {
        "title": "Add H2 Subheadings",
        "difficulty": "Easy",
        "time": "15 minutes",
        "impact": "Medium",
        "summary": "H2 tags structure your content into sections, helping Google understand all the sub-topics you cover. They also improve readability and keep users on the page longer.",
        "steps": [
            "Identify the main sections/topics on this page",
            "Write an H2 for each section that naturally includes related keywords",
            "Aim for one H2 every 200–300 words of content",
            "Make H2s descriptive — avoid generic labels like 'More Info'"
        ],
        "code": """<!-- Add H2s to structure your content -->
<h1>Organic Coffee Beans — Fresh Roasted Weekly</h1>

<h2>Our Single-Origin Coffee Collection</h2>
<p>We source directly from farms...</p>

<h2>How We Roast — The FreshRoast Process</h2>
<p>Every batch is roasted to order...</p>

<h2>Free UK Delivery on All Orders Over £25</h2>
<p>We ship Monday to Friday...</p>

<h2>What Our Customers Say</h2>
<!-- testimonials here -->

<h2>Frequently Asked Questions</h2>
<!-- FAQ items here -->""",
        "do": ["Include keywords naturally in H2s", "Make them descriptive and benefit-focused", "Use H2s for FAQ questions"],
        "dont": ["Don't use H2 just as decorative dividers", "Don't repeat the same phrase as H1"],
    },

    # ── IMAGES ─────────────────────────────────────────────────────────────────

    "images missing alt": {
        "title": "Add Alt Text to Images",
        "difficulty": "Medium",
        "time": "20–60 minutes",
        "impact": "High",
        "summary": "Alt text describes images for screen readers (accessibility) and helps Google understand image content (SEO). Missing alt text also means missing image search traffic.",
        "steps": [
            "Audit all images on the page",
            "For each image, write a concise description of what it shows",
            "Include your keyword naturally if the image is relevant to it",
            "Leave alt empty (alt='') for purely decorative images",
            "In CMS (WordPress/Shopify): edit each image's alt text field",
            "In HTML: add alt attribute directly to <img> tags"
        ],
        "code": """<!-- BEFORE (missing alt): -->
<img src="coffee-beans.jpg">

<!-- AFTER (descriptive alt text): -->
<img src="coffee-beans.jpg" alt="Fresh roasted Colombian coffee beans in a wooden bowl">

<!-- Keyword-rich but natural: -->
<img src="team-photo.jpg" alt="FreshRoast team at our London roastery, 2024">

<!-- Decorative image (intentionally empty alt): -->
<img src="divider-line.svg" alt="" role="presentation">

<!-- In WordPress: Media → Edit → Alt Text field
     In Shopify:  Products → Images → Edit Alt Text
     In Webflow:  Click image → Settings → Alt Text -->

<!-- Bulk fix in Python (if you manage HTML): -->
# Find all images missing alt and flag them for manual review""",
        "do": ["Be specific and descriptive", "Include keyword if naturally relevant", "Use empty alt='' for decorative images"],
        "dont": ["Don't stuff keywords: 'coffee beans buy cheap coffee beans UK'", "Don't use 'image of' or 'photo of'", "Don't use the filename as alt text"],
    },

    "images missing width/height": {
        "title": "Add Width & Height to Images",
        "difficulty": "Easy",
        "time": "30 minutes",
        "impact": "Medium",
        "summary": "Without width/height attributes, the browser doesn't know how much space to reserve for images. When they load, content jumps around — this is called Cumulative Layout Shift (CLS), a Core Web Vital that affects Google rankings.",
        "steps": [
            "Find the actual dimensions of each image (right-click → Get Info / Properties)",
            "Add explicit width and height attributes matching the image's natural dimensions",
            "Use CSS to make them responsive: img { max-width: 100%; height: auto; }",
            "Test CLS score in PageSpeed Insights after fixing"
        ],
        "code": """<!-- BEFORE (causes layout shift): -->
<img src="coffee-hero.jpg" alt="Premium coffee beans">

<!-- AFTER (browser reserves exact space): -->
<img src="coffee-hero.jpg" alt="Premium coffee beans" width="1200" height="630">

<!-- CSS to keep them responsive while preventing CLS: -->
<style>
  img {
    max-width: 100%;
    height: auto;  /* overrides the height attribute for responsive display */
  }
</style>

<!-- In Next.js — use the Image component (handles this automatically): -->
import Image from 'next/image'
<Image src="/coffee.jpg" alt="Coffee" width={1200} height={630} />

<!-- Check your CLS score: -->
<!-- https://pagespeed.web.dev — target CLS < 0.1 -->""",
        "do": ["Use the image's natural pixel dimensions", "Add CSS height:auto for responsiveness", "Verify with PageSpeed Insights"],
        "dont": ["Don't guess dimensions — use actual pixel values", "Don't set arbitrary dimensions that distort the image"],
    },

    "Only X/Y images use lazy loading": {
        "title": "Add Lazy Loading to Images",
        "difficulty": "Easy",
        "time": "15 minutes",
        "impact": "Medium",
        "summary": "Lazy loading delays loading of off-screen images until the user scrolls to them. This speeds up initial page load, improving both user experience and Core Web Vitals.",
        "steps": [
            "Identify images that are below the fold (not visible without scrolling)",
            "Add loading='lazy' to all below-fold images",
            "Leave above-fold images without lazy loading (or use loading='eager')",
            "Never lazy-load the Largest Contentful Paint (LCP) image"
        ],
        "code": """<!-- Above-the-fold hero image — DO NOT lazy load -->
<img src="hero.jpg" alt="Hero" width="1200" height="600">

<!-- All below-fold images — ADD lazy loading -->
<img src="product-1.jpg" alt="Product 1" width="400" height="400" loading="lazy">
<img src="product-2.jpg" alt="Product 2" width="400" height="400" loading="lazy">
<img src="team-photo.jpg" alt="Team"    width="800" height="400" loading="lazy">

<!-- In WordPress: Images added after WP 5.5 are lazy-loaded automatically -->
<!-- In React: -->
<img src={product.img} alt={product.name} loading="lazy" />

<!-- Vanilla JS fallback for older browsers: -->
<script>
  if ('loading' in HTMLImageElement.prototype) {
    // Browser supports native lazy loading
  } else {
    // Load lazysizes.js polyfill
  }
</script>""",
        "do": ["Lazy load all below-fold images", "Test on slow 3G in Chrome DevTools", "Check PageSpeed score improves"],
        "dont": ["Don't lazy-load the first visible image", "Don't lazy-load all images including hero"],
    },

    # ── TECHNICAL ──────────────────────────────────────────────────────────────

    "NOT using HTTPS": {
        "title": "Migrate to HTTPS (SSL Certificate)",
        "difficulty": "Medium",
        "time": "1–4 hours",
        "impact": "Critical",
        "summary": "HTTPS is a confirmed Google ranking factor. Without it, browsers show a 'Not Secure' warning which destroys user trust. Free SSL certificates are available for all sites.",
        "steps": [
            "Get a free SSL certificate (Let's Encrypt via your host, or Cloudflare)",
            "Install the certificate on your server (most hosts have a 1-click option)",
            "Update all internal links from http:// to https://",
            "Set up 301 redirects from http:// to https:// for all URLs",
            "Update your canonical tags and sitemap to use https://",
            "Update Google Search Console and Analytics to use the https version"
        ],
        "code": """# Method 1: Cloudflare (free, easiest)
# 1. Sign up at cloudflare.com
# 2. Add your site and update nameservers
# 3. Enable 'Full SSL' in Cloudflare SSL/TLS settings
# 4. Enable 'Always Use HTTPS' redirect

# Method 2: Let's Encrypt via Certbot (Linux server)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yoursite.com -d www.yoursite.com

# Method 3: cPanel / Hosting control panel
# Hosting dashboard → SSL/TLS → Let's Encrypt → Install

# After installing SSL, set up 301 redirect in .htaccess (Apache):
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Or in Nginx config:
server {
    listen 80;
    server_name yoursite.com;
    return 301 https://$server_name$request_uri;
}""",
        "do": ["Redirect ALL http URLs to https with 301", "Update sitemap and GSC property", "Test with SSL checker: ssllabs.com/ssltest"],
        "dont": ["Don't use self-signed certificates in production", "Don't mix http and https content (mixed content errors)"],
    },

    "Load time too slow": {
        "title": "Improve Page Load Speed",
        "difficulty": "Medium",
        "time": "2–8 hours",
        "impact": "High",
        "summary": "Page speed is a direct Google ranking factor. Every 1 second of delay reduces conversions by ~7%. Target under 3 seconds for acceptable speed, under 1.5s for excellent.",
        "steps": [
            "Run PageSpeed Insights to identify your specific bottlenecks",
            "Compress and resize images (biggest impact)",
            "Enable browser caching and GZIP compression on your server",
            "Minify CSS, JavaScript, and HTML",
            "Move render-blocking scripts to bottom of page or add defer/async",
            "Consider a CDN (Content Delivery Network) for global audiences"
        ],
        "code": """<!-- 1. Defer non-critical JavaScript -->
<script src="analytics.js" defer></script>
<script src="chat-widget.js" async></script>

<!-- 2. Preload critical resources -->
<link rel="preload" href="hero.jpg" as="image">
<link rel="preload" href="main.css" as="style">

<!-- 3. Modern image formats -->
<picture>
  <source srcset="hero.webp" type="image/webp">
  <source srcset="hero.avif" type="image/avif">
  <img src="hero.jpg" alt="Hero image" width="1200" height="600">
</picture>

# 4. GZIP in .htaccess
AddOutputFilterByType DEFLATE text/html text/css application/javascript

# 5. Browser caching in .htaccess
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/jpg "access 1 year"
  ExpiresByType text/css "access 1 month"
  ExpiresByType application/javascript "access 1 month"
</IfModule>""",
        "do": ["Test before and after each change", "Target LCP < 2.5s", "Use CDN for images and static assets"],
        "dont": ["Don't optimise without measuring first", "Don't disable caching completely"],
    },

    "No structured data": {
        "title": "Add Schema.org Structured Data",
        "difficulty": "Medium",
        "time": "30–60 minutes",
        "impact": "Medium",
        "summary": "Structured data (Schema.org) helps Google display rich results — star ratings, FAQs, prices, breadcrumbs — directly in search. These dramatically improve click-through rate.",
        "steps": [
            "Decide which schema type fits your page (Article, Product, FAQ, LocalBusiness, etc.)",
            "Generate the JSON-LD code for your schema type",
            "Add it inside a <script type='application/ld+json'> tag in your <head>",
            "Test using Google's Rich Results Test: search.google.com/test/rich-results",
            "Monitor in Search Console under 'Enhancements'"
        ],
        "code": """<!-- FAQ Schema (shows expandable Q&As in Google) -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How fresh are your coffee beans?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "All our beans are roasted to order and dispatched within 24 hours."
      }
    },
    {
      "@type": "Question",
      "name": "Do you offer free delivery?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes, free UK delivery on all orders over £25."
      }
    }
  ]
}
</script>

<!-- Product Schema (shows price, rating in search) -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Colombian Coffee Beans 250g",
  "description": "Single-origin Colombian coffee...",
  "brand": {"@type": "Brand", "name": "FreshRoast"},
  "offers": {
    "@type": "Offer",
    "price": "12.99",
    "priceCurrency": "GBP",
    "availability": "https://schema.org/InStock"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "127"
  }
}
</script>""",
        "do": ["Test with Google's Rich Results Test before deploying", "Use FAQ schema for any Q&A content", "Add Product schema to all e-commerce product pages"],
        "dont": ["Don't add fake reviews or ratings", "Don't mark up content that isn't visible on the page"],
    },

    "Missing HTML lang attribute": {
        "title": "Add HTML lang Attribute",
        "difficulty": "Easy",
        "time": "5 minutes",
        "impact": "Medium",
        "summary": "The lang attribute tells browsers and search engines what language your page is in. Screen readers use it to select the right pronunciation. Google uses it for international SEO.",
        "steps": [
            "Open your HTML template or theme file",
            "Find the opening <html> tag",
            "Add the lang attribute with the appropriate language code",
            "Use a specific locale code if you have multilingual content"
        ],
        "code": """<!-- English (UK) -->
<html lang="en-GB">

<!-- English (US) -->
<html lang="en-US">

<!-- Spanish -->
<html lang="es">

<!-- French -->
<html lang="fr">

<!-- German -->
<html lang="de">

<!-- Hindi -->
<html lang="hi">

<!-- Arabic (right-to-left) -->
<html lang="ar" dir="rtl">

<!-- In WordPress: set via Settings → General → Site Language
     In Webflow:   Project Settings → Internationalization
     In Shopify:   Online Store → Preferences → Store language -->""",
        "do": ["Use the correct BCP47 language code", "Add both language and region code (en-GB, not just en)", "Add dir='rtl' for Arabic, Hebrew, etc."],
        "dont": ["Don't use country codes alone (GB, US) — use language codes (en-GB)", "Don't use the same lang for pages in different languages"],
    },

    # ── LINKS ──────────────────────────────────────────────────────────────────

    "links have no anchor text": {
        "title": "Add Descriptive Anchor Text to Links",
        "difficulty": "Easy",
        "time": "20 minutes",
        "impact": "Medium",
        "summary": "Links with no anchor text give Google no context about where they lead. They also fail accessibility requirements (screen reader users hear 'link' with no description).",
        "steps": [
            "Find all empty or icon-only links on the page",
            "Add descriptive text between the <a> tags",
            "For icon links, use aria-label to describe the destination",
            "For image links, ensure the image has descriptive alt text"
        ],
        "code": """<!-- BEFORE (empty link): -->
<a href="/products/coffee"><img src="arrow.svg"></a>

<!-- AFTER (descriptive): -->
<a href="/products/coffee">Shop our coffee collection</a>

<!-- Icon-only link — use aria-label: -->
<a href="https://twitter.com/brand" aria-label="Follow us on Twitter">
  <svg><!-- twitter icon --></svg>
</a>

<!-- Image link — alt text becomes anchor text: -->
<a href="/products/">
  <img src="products.jpg" alt="View our full coffee product range">
</a>

<!-- Bad anchor text examples to fix: -->
<a href="/contact">Click here</a>  → <a href="/contact">Contact our team</a>
<a href="/guide">Read more</a>     → <a href="/guide">Read our beginner's coffee guide</a>
<a href="/shop">Here</a>           → <a href="/shop">Shop coffee beans</a>""",
        "do": ["Be specific about the destination", "Include keywords naturally", "Make sense out of context"],
        "dont": ["Don't use 'click here', 'read more', 'here'", "Don't repeat the same anchor text for different pages"],
    },

    "Very few internal links": {
        "title": "Add More Internal Links",
        "difficulty": "Medium",
        "time": "30 minutes",
        "impact": "High",
        "summary": "Internal links pass PageRank between pages, help Google discover and crawl your content, and keep users on your site longer. Most pages should have 5–15 internal links.",
        "steps": [
            "Identify related pages on your site that this page could link to",
            "Find natural places in your content to add contextual links",
            "Add links to your most important pages (pillar content)",
            "Ensure every important page is reachable within 3 clicks from the homepage",
            "Consider adding a 'Related Articles' or 'You might also like' section"
        ],
        "code": """<!-- Contextual internal links in body copy -->
<p>
  Our <a href="/brewing-guide/">coffee brewing guide</a> covers everything from
  French press to espresso. If you're new to specialty coffee, start with our
  <a href="/beginners-guide/">beginner's introduction</a>.
</p>

<!-- Related content section -->
<section>
  <h2>Related Articles</h2>
  <ul>
    <li><a href="/coffee-origins/colombia/">Colombia: The Home of Coffee</a></li>
    <li><a href="/how-to/french-press/">How to Brew the Perfect French Press</a></li>
    <li><a href="/coffee-varieties/arabica-vs-robusta/">Arabica vs Robusta Explained</a></li>
  </ul>
</section>

<!-- Breadcrumb navigation (also improves SEO) -->
<nav aria-label="Breadcrumb">
  <a href="/">Home</a> →
  <a href="/coffee-beans/">Coffee Beans</a> →
  <span>Colombian Single-Origin</span>
</nav>""",
        "do": ["Link to relevant, related content", "Use descriptive anchor text", "Link to your most important pages from every page"],
        "dont": ["Don't add links that don't make sense contextually", "Don't have more than 100 links on one page"],
    },

    # ── KEYWORDS ───────────────────────────────────────────────────────────────

    "Top keywords not in title": {
        "title": "Add Primary Keyword to Title Tag",
        "difficulty": "Easy",
        "time": "10 minutes",
        "impact": "High",
        "summary": "Google gives extra weight to keywords that appear in the title tag. Your primary keyword should appear near the beginning of the title for maximum SEO impact.",
        "steps": [
            "Identify your primary keyword (the main term users search to find this page)",
            "Rewrite your title tag to naturally include this keyword",
            "Put the keyword as close to the beginning as possible",
            "Keep total length under 60 characters"
        ],
        "code": """<!-- Step 1: Find your primary keyword
     - What would someone type to find this page?
     - Use Google autocomplete to see popular variations
     - Check which keyword brings you traffic in Google Search Console -->

<!-- BEFORE (keyword not in title): -->
<title>Our Story — FreshRoast Coffee Company</title>

<!-- AFTER (keyword first): -->
<title>Buy Coffee Beans Online | FreshRoast — Free UK Delivery</title>

<!-- More examples: -->
<!-- Before: --> <title>Welcome to Our Shop</title>
<!-- After:  --> <title>Coffee Beans UK — Shop 20+ Varieties | FreshRoast</title>

<!-- Before: --> <title>Blog Post #42</title>
<!-- After:  --> <title>How to Make Cold Brew Coffee at Home in 5 Steps</title>""",
        "do": ["Put the keyword near the start", "Use the exact keyword phrase people search for", "Check Google Search Console for actual queries"],
        "dont": ["Don't sacrifice readability to force a keyword", "Don't use the keyword more than once in the title"],
    },

    "Low word count": {
        "title": "Increase Page Content Length",
        "difficulty": "Hard",
        "time": "2–8 hours",
        "impact": "High",
        "summary": "Thin content (under 500 words) is harder to rank. Google wants to serve comprehensive answers. Long-form content (1500+ words) consistently outranks thin pages for competitive keywords.",
        "steps": [
            "Research what topics top-ranking pages cover for your target keyword",
            "Identify what questions users have that your page doesn't answer",
            "Add new sections: How it works, FAQ, Use cases, Examples, Case studies",
            "Add an FAQ section using common 'People Also Ask' questions from Google",
            "Add a comparison table if relevant",
            "Ensure every word adds value — avoid padding"
        ],
        "code": """<!-- Content structure for a 1500+ word page: -->

<h1>Primary Keyword — Main Topic</h1>
<!-- 100-word intro: what this page covers -->

<h2>What is [Topic]?</h2>
<!-- 200 words: clear definition -->

<h2>How [Topic] Works</h2>
<!-- 300 words: step-by-step explanation -->

<h2>Benefits of [Topic]</h2>
<!-- 200 words: value proposition -->

<h2>[Topic] vs [Alternative] — Comparison</h2>
<!-- 200 words + comparison table -->

<h2>Common [Topic] Mistakes to Avoid</h2>
<!-- 200 words: builds authority -->

<h2>Frequently Asked Questions</h2>
<!-- 5-10 Q&As: targets "People Also Ask" in Google -->

<h2>Summary</h2>
<!-- 100 words: recap + CTA -->

<!-- Total: ~1500 words minimum
     Target: 2000+ for competitive keywords -->""",
        "do": ["Research the top 10 ranking pages for your keyword", "Answer every question your user might have", "Use headings to make long content scannable"],
        "dont": ["Don't pad with repeated or irrelevant content", "Don't sacrifice quality for quantity"],
    },
}


def get_fix_guide(issue_message: str) -> dict | None:
    """
    Find the best fix guide for an issue message.
    Tries exact match first, then keyword matching.
    """
    msg_lower = issue_message.lower()

    # Exact match
    for key, guide in FIX_GUIDES.items():
        if key.lower() in msg_lower:
            return guide

    # Keyword match
    keyword_map = {
        "title": ["title too short", "title too long", "no <title>", "title tag"],
        "description": ["meta description", "no meta description", "description too"],
        "canonical": ["canonical"],
        "viewport": ["viewport"],
        "noindex": ["noindex", "no index"],
        "open graph": ["open graph", "og:title", "og:image", "missing og"],
        "h1": ["no h1", "h1 tag", "multiple h1"],
        "h2": ["no h2", "h2 tags"],
        "alt text": ["alt text", "missing alt", "images missing alt"],
        "width/height": ["width/height", "missing width", "layout shift"],
        "lazy": ["lazy loading", "lazy load"],
        "https": ["https", "ssl", "secure"],
        "speed": ["load time", "page speed", "too slow"],
        "schema": ["structured data", "schema", "json-ld"],
        "lang": ["html lang", "lang attribute"],
        "anchor": ["anchor text", "no anchor", "generic text"],
        "internal links": ["internal links", "few internal"],
        "keyword": ["keyword not in title", "keywords not in title"],
        "word count": ["word count", "low word count", "thin content"],
    }

    for guide_key, keywords in keyword_map.items():
        if any(kw in msg_lower for kw in keywords):
            # Find matching guide
            for fix_key, guide in FIX_GUIDES.items():
                if guide_key.lower() in fix_key.lower():
                    return guide

    return None
