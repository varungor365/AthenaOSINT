"""
Instagram Scraper Module (Advanced).
Uses Instaloader with Authentication to scrape Profiles, Stories, and Media.
"4K Stogram" Alternative.
"""
from loguru import logger
from core.engine import Profile
from config import get_config
import instaloader
import os

# Metadata
META = {
    'name': 'instagram',
    'description': 'Instagram Scraper (Auth supported)',
    'category': 'Social Media',
    'risk': 'medium', 
    'emoji': '📸'
}

def scan(target: str, profile: Profile):
    """
    Scrapes Instagram. Checks for credentials in .env.
    """
    username = target
    if 'instagram.com' in target:
        # Extract username from URL
        parts = target.split('/')
        if parts[-1] == '': parts.pop()
        username = parts[-1]
    
    logger.info(f"[Instagram] Target: {username}")
    
    # 1. Setup Instaloader
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False, 
        save_metadata=False,
        compress_json=False
    )
    
    # 2. Login (Optional but recommended for Stories/Private)
    config = get_config()
    ig_user = config.get('INSTAGRAM_USER') or os.getenv('INSTAGRAM_USER')
    ig_pass = config.get('INSTAGRAM_PASSWORD') or os.getenv('INSTAGRAM_PASSWORD')
    
    is_logged_in = False
    
    if ig_user and ig_pass:
        try:
            logger.info(f"[Instagram] Attempting login as {ig_user}...")
            L.login(ig_user, ig_pass)
            is_logged_in = True
            logger.success("[Instagram] Login successful.")
        except Exception as e:
            logger.warning(f"[Instagram] Login failed: {e}")
    else:
        logger.info("[Instagram] No credentials found. Running in Anonymous mode (Public info only).")

    try:
        # 3. Load Profile
        prof = instaloader.Profile.from_username(L.context, username)
        
        # 4. Extract Data
        data = {
            'username': prof.username,
            'full_name': prof.full_name,
            'biography': prof.biography,
            'followers': prof.followers,
            'followees': prof.followees,
            'is_verified': prof.is_verified,
            'is_private': prof.is_private,
            'profile_pic_url': prof.profile_pic_url,
            'external_url': prof.external_url
        }
        
        profile.add_metadata({'instagram_profile': data})
        
        # Add PFP as an image "artifact" (conceptually)
        if prof.profile_pic_url:
            profile.add_metadata({'image_url': prof.profile_pic_url})

        # 5. Get Stories (If logged in)
        if is_logged_in and prof.has_public_story:
            logger.info("[Instagram] Fetching Stories...")
            stories = []
            for story in L.get_stories(userids=[prof.userid]):
                for item in story.get_items():
                    stories.append({
                        'date': str(item.date),
                        'url': item.url,
                        'type': 'video' if item.is_video else 'image'
                    })
            profile.add_metadata({'instagram_stories': stories})
            logger.success(f"[Instagram] Found {len(stories)} stories.")

        # 6. Get Recent Posts
        logger.info("[Instagram] Fetching recent posts...")
        posts = []
        count = 0
        for post in prof.get_posts():
            if count >= 10: break
            posts.append({
                'date': str(post.date),
                'caption': post.caption[:200] if post.caption else "",
                'likes': post.likes,
                'comments': post.comments,
                'url': post.url # High-res URL
            })
            count += 1
            
        profile.add_metadata({'instagram_posts': posts})
        logger.success(f"[Instagram] Scraped {len(posts)} recent posts.")

    except Exception as e:
        logger.error(f"[Instagram] Scraping failed: {e}")
        profile.add_error('instagram', str(e))
