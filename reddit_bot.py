import textwrap
from PIL import Image, ImageDraw, ImageFont
import urllib
import praw
import config
import time
import os
import uuid

import mysql.connector


class Meme:
    basewidth = 1200
    fontBase = 100
    letSpacing = 9
    fill = (255, 255, 255)
    stroke_fill = (0, 0, 0)
    lineSpacing = 10
    stroke_width = 9
    fontfile = './impact.ttf'

    def __init__(self, caption, image):
        self.img = self.createImage(image)
        self.d = ImageDraw.Draw(self.img)

        self.splitCaption = textwrap.wrap(caption, width=20)
        self.splitCaption.reverse()

        # If there is only one line, make the text a bit larger
        fontSize = self.fontBase + \
            10 if len(self.splitCaption) <= 1 else self.fontBase
        self.font = ImageFont.truetype(font=self.fontfile, size=fontSize)
        # self.shadowFont = ImageFont.truetype(font='./impact.ttf', size=fontSize+10)

    def draw(self):
        '''
        Draws text onto this objects img object
        :return: A pillow image object with text drawn onto the image
        '''
        (iw, ih) = self.img.size
        (_, th) = self.d.textsize(
            self.splitCaption[0], font=self.font)  # Height of the text
        # The starting y position to draw the last line of text. Text in drawn from the bottom line up
        y = (ih - (ih / 10)) - (th / 2)

        for cap in self.splitCaption:  # For each line of text
            # Getting the position of the text
            (tw, _) = self.d.textsize(cap, font=self.font)
            # Center the text and account for the spacing between letters
            x = ((iw - tw) - (len(cap) * self.letSpacing))/2

            self.drawLine(x=x, y=y, caption=cap)
            y = y - th - self.lineSpacing  # Next block of text is higher up

        wpercent = ((self.basewidth/2) / float(self.img.size[0]))
        hsize = int((float(self.img.size[1]) * float(wpercent)))
        return self.img.resize((int(self.basewidth/2), hsize))

    def createImage(self, image):
        '''
        Resizes the image to a resonable standard size
        :param image: Path to an image file
        :return: A pil image object
        '''
        img = Image.open(image)
        wpercent = (self.basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        return img.resize((self.basewidth, hsize))

    def drawLine(self, x, y, caption):
        '''
        The text gets split into multiple lines if it is wider than the image. This function draws a single line
        :param x: The starting x coordinate of the text
        :param y: The starting y coordinate of the text
        :param caption: The text to write on the image
        :return: None
        '''
        for idx in range(0, len(caption)):  # For each letter in the line of text
            char = caption[idx]
            w, h = self.font.getsize(char)  # width and height of the letter
            self.d.text(
                (x, y),
                char,
                fill=self.fill,
                stroke_width=self.stroke_width,
                font=self.font,
                stroke_fill=self.stroke_fill
            )  # Drawing the text character by character. This way spacing can be added between letters
            # The next character must be drawn at an x position more to the right
            x += w + self.letSpacing


def bot_login():
    print(">>> Logging in to Reddit Meme Bot...")
    r = praw.Reddit(username=config.username,
                    password=config.password,
                    client_id=config.client_id,
                    client_secret=config.client_secret,
                    user_agent=("The Reddit Commenter v1.0"))
    print(">>> Logged in to Reddit Meme Bot")

    return r


def run_bot(r):
    for mention in r.inbox.unread(limit=None):
        if "u/CommentMemeGen" in mention.body:
            print(">>> Reddit Meme Bot has been mentioned in a post")
            parent_id = (mention.parent_id)

            comment = r.comment(id=parent_id)
            submission = (comment.submission)
            url = submission.url
            meme_text = comment.body
            reddit_url = ((comment.permalink))
            mention.mark_read()
            
            
            
            
            #Filter for videos and posts that do not contain images
            #ERROR CATCHING CHANGES:
            #---If there are too many characters in comment body
            #---If the post is not in the right format or is a video
            #---If the post is nsfw
            
            
            if url.endswith("jpg") or url.endswith("jpeg") or url.endswith("png"):
                photo_uuid = str(uuid.uuid4())

                
                urllib.request.urlretrieve(url, ("postsToMeme/" + photo_uuid + ".jpeg"))
                
                caption = meme_text
                image = ("postsToMeme/" + photo_uuid + '.jpeg')
                outputImage = ('postsMemed/' + photo_uuid + '.jpeg')

                meme = Meme(caption, image)
                img = meme.draw()
                print(">>> Generating Meme...")
                if img.mode in ("RGBA", "P"):  # Without this the code can break sometimes
                    img = img.convert("RGB")
                img.save(outputImage, optimize=True, quality=80)
                
                
                addPhotoToDB(photo_uuid, reddit_url)
                mention.reply(body="https://CommentMemeGen" + reddit_url)
                print(">>> Meme Generated at url: " + ("https://CommentMemeGen" + reddit_url))
                
            else:
                print(">>> Cannot Convert Image")
           

def addPhotoToDB(photo_uuid, reddit_url):
    memed_photos_db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="ObjectRecognition27!",
        database="sys"
    )
    
    mycursor = memed_photos_db.cursor()
    
    sql = ("INSERT INTO sys.memed_photos VALUES (%s, %s)")
    val = (photo_uuid, reddit_url)
    
    mycursor.execute(sql, val)
    memed_photos_db.commit()
    print(">>> Saved to Database")
    
r = bot_login()

while True:
    run_bot(r)
