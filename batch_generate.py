#!/usr/bin/env python3
"""
Batch Video Generation Example
Generate multiple videos at once from a list of topics
"""

from video_pipeline import VideoGenerationPipeline
import time

def batch_generate_videos(topics: list, output_dir: str = "batch_output"):
    """
    Generate multiple videos from a list of topics
    
    Args:
        topics: List of video topics
        output_dir: Directory to save all videos
    """
    pipeline = VideoGenerationPipeline(output_dir=output_dir)
    
    results = []
    total_topics = len(topics)
    
    print(f"\n🚀 Starting batch generation for {total_topics} videos...\n")
    
    for i, topic in enumerate(topics, 1):
        print(f"\n{'='*60}")
        print(f"📹 Video {i}/{total_topics}: {topic}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            video_path = pipeline.generate_video(topic)
            elapsed = time.time() - start_time
            
            results.append({
                "topic": topic,
                "status": "success",
                "video_path": video_path,
                "time_taken": elapsed
            })
            
            print(f"✅ Completed in {elapsed:.2f} seconds")
            
        except Exception as e:
            elapsed = time.time() - start_time
            
            results.append({
                "topic": topic,
                "status": "failed",
                "error": str(e),
                "time_taken": elapsed
            })
            
            print(f"❌ Failed: {e}")
        
        # Small delay between videos to avoid rate limits
        if i < total_topics:
            print("\n⏸️  Pausing 5 seconds before next video...")
            time.sleep(5)
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 BATCH GENERATION SUMMARY")
    print(f"{'='*60}")
    
    successful = sum(1 for r in results if r["status"] == "success")
    failed = total_topics - successful
    
    print(f"\n✅ Successful: {successful}/{total_topics}")
    print(f"❌ Failed: {failed}/{total_topics}")
    
    total_time = sum(r["time_taken"] for r in results)
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    print(f"⚡ Average time per video: {total_time/total_topics:.2f} seconds")
    
    print("\nDetailed Results:")
    for r in results:
        status_icon = "✅" if r["status"] == "success" else "❌"
        print(f"\n{status_icon} {r['topic']}")
        if r["status"] == "success":
            print(f"   Path: {r['video_path']}")
        else:
            print(f"   Error: {r['error']}")
        print(f"   Time: {r['time_taken']:.2f}s")
    
    return results


def main():
    """Example usage"""
    
    # Example topics for a tutorial series
    topics = [
        "What is Machine Learning?",
        "How Neural Networks Work",
        "Introduction to Deep Learning",
        "Computer Vision Basics",
        "Natural Language Processing Explained"
    ]
    
    print("""
╔══════════════════════════════════════════════════════════╗
║         BATCH VIDEO GENERATION                           ║
║         Generate Multiple Videos at Once                 ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    print("Topics to generate:")
    for i, topic in enumerate(topics, 1):
        print(f"  {i}. {topic}")
    
    proceed = input("\nProceed with batch generation? (y/n): ").strip().lower()
    
    if proceed == 'y':
        results = batch_generate_videos(topics)
        
        print("\n🎉 Batch generation complete!")
        print(f"📁 Videos saved in: batch_output/")
    else:
        print("Cancelled.")


if __name__ == "__main__":
    main()