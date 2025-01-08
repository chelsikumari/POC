import mysql.connector
from mysql.connector import Error
import re
from typing import List, Dict
import re
from typing import List, Dict

def extract_tags_from_question(question: str) -> List[str]:
    """
    Extracts potential tags from the given question.
    """
    words = re.findall(r'\b\w+\b', question.lower())
    common_words = {'what', 'is', 'how', 'why', 'a', 'the', 'and', 'in', 'of', 'to', 'on', 'for'}
    tags = [word for word in words if word not in common_words]
    return tags

def fetch_related_videos(tags: List[str], db_config: Dict) -> List[Dict]:
    """
    Fetches related videos based on tags from a MySQL database.
    :param tags: List of tags extracted from the question.
    :param db_config: Dictionary with MySQL connection details.
    :return: List of dictionaries containing video metadata.
    """
    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Prepare SQL query
        query = f"""
                SELECT video_url ,thumbnail_url 
                FROM learning_bytes
            WHERE {' OR '.join(['tags LIKE %s'] * len(tags))}
            ORDER BY created_on DESC
            LIMIT 10;
        """
        params = [f"%{tag}%" for tag in tags]

        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Map results to dictionaries
        related_videos = [
            {
                # "id": row[0],
                # "title": row[1],
                # "tags": row[2],
                # "description": row[3],
                "video_url": row[0],
                "thumbnail_url": row[1]
            }
            for row in rows
        ]

    except Error as e:
        print(f"Error: {e}")
        related_videos = []

    finally:
        # Close the connection
        if connection.is_connected(): 
            cursor.close()
            connection.close()

    return related_videos

def suggest_videos(question: str, db_config: Dict) -> List[Dict]:
    """
    Suggests related videos based on the user's question.
    :param question: The question asked by the user.
    :param db_config: Dictionary with MySQL connection details.
    :return: List of suggested videos.
    """
    tags = extract_tags_from_question(question)
    if not tags:
        return [{"message": "No relevant tags found for the question."}]
    
    related_videos = fetch_related_videos(tags, db_config)
    if not related_videos:
        return [{"message": "No related videos found for the given tags."}]
    
    return related_videos

# Example usage
# if __name__ == "__main__":
#     question = "What are gears?"
#     db_config = {
#     "host": "`demo-db.chsy2gu0svmq.us-east-1.rds.amazonaws.com`",
#     "user": "admin",
#     "password": "gXXk1VwhGlEyo9PKHUmH",
#     "database": "skillupdb" 
#     }
    
def videosLinks(question,db_config):
    return suggest_videos(question, db_config)
    
   