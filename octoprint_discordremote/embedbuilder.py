import datetime
import io
import math
import zipfile
import os

DISCORD_MAX_FILE_SIZE = 5 * 1024 * 1024

COLOR_SUCCESS = 0x00AE86
COLOR_ERROR = 0xE84A4A
COLOR_INFO = 0xF2E82B

MAX_TITLE = 256
MAX_VALUE = 1024
MAX_DESCRIPTION = 2048
MAX_EMBED_LENGTH = 6000
MAX_NUM_FIELDS = 25


def embed_simple(author, title=None, description=None, color=None, snapshot=None):
    builder = EmbedBuilder()
    if color:
        builder.set_color(color)
    if title:
        builder.set_title(title)
    if description:
        builder.set_description(description)
    if snapshot:
        builder.set_image(snapshot)
    if author:
        builder.set_author(author)
    return builder.get_embeds()


def success_embed(author, title=None, description=None, snapshot=None):
    return embed_simple(author, title, description, COLOR_SUCCESS, snapshot)


def error_embed(author, title=None, description=None, snapshot=None):
    return embed_simple(author, title, description, COLOR_ERROR, snapshot)


def info_embed(author, title=None, description=None, snapshot=None):
    return embed_simple(author, title, description, COLOR_INFO, snapshot)

def upload_file(path, author=None):
    file_name = os.path.basename(path)
    file_stat = os.stat(path)
    file_size = file_stat.st_size

    if file_size < DISCORD_MAX_FILE_SIZE:
        fl = (file_name, open(path))
        embeds = EmbedBuilder() \
            .set_author(author) \
            .set_title("Uploaded %s" % file_name) \
            .get_embeds()
        return [fl], embeds

    else:
        with zipfile.ZipFile("temp.zip", 'w') as zip_file:
            zip_file.write(path, file_name)

        # Get the compressed file size
        file_stat = os.stat("temp.zip")
        file_size = file_stat.st_size
        num_parts = int(math.ceil(float(file_size) / DISCORD_MAX_FILE_SIZE))

        embedbuilder = EmbedBuilder() \
            .set_author(author) \
            .set_title("Uploaded %s in %i parts" % (file_name, num_parts))

        files = []
        with open("temp.zip", 'rb') as zip_file:
            i = 1
            while True:
                part_name = "%s.zip.%.03i" % (file_name, i)
                part_file = io.BytesIO()
                data = zip_file.read(DISCORD_MAX_FILE_SIZE)
                if len(data) == 0:
                    break
                part_file.write(data)
                part_file.seek(0)
                files.append((part_name, part_file))
                i += 1

        os.remove("temp.zip")
        return files, embedbuilder.get_embeds()


class EmbedBuilder:
    def __init__(self):
        self.color = COLOR_INFO
        self.embeds = [Embed()]
        self.timestamp = True
        self.author = None

    def set_color(self, color):
        self.color = color
        return self

    def set_title(self, title):
        if title is None:
            title = ""
        elif len(title) > MAX_TITLE:
            title = title[0:MAX_TITLE - 3] + "..."

        while not self.embeds[-1].set_title(title):
            self.embeds.append(Embed())

        return self

    def set_description(self, description):
        if description is None:
            description = None
        elif len(description) > MAX_DESCRIPTION:
            description = description[0:MAX_DESCRIPTION - 3] + "..."

        while not self.embeds[-1].set_description(description):
            self.embeds.append(Embed())

        return self

    def set_author(self, name, url=None, icon_url=None):
        if name is None:
            self.author = None
            return self
        if len(name) > MAX_TITLE:
                name = name[0:MAX_TITLE - 3] + "..."
        self.author = {'name': name}
        if url:
            self.author['url'] = url
        if icon_url:
            self.author['icon_url'] = icon_url
        return self

    def add_field(self, title, text, inline=False):
        if title is None or len(str(title)) == 0:
            title = "DEVERROR: Passed an invalid title"
        if text is None or len(str(text)) == 0:
            text = "DEVERROR: Passed an invalid text"

        if len(str(title)) > MAX_TITLE:
            title = title[0:MAX_TITLE - 3] + "..."
        if len(str(text)) > MAX_VALUE:
            text = text[0:MAX_VALUE - 3] + "..."

        while not self.embeds[-1].add_field({'name': str(title),
                                             'value': str(text),
                                             'inline': inline}):
            self.embeds.append(Embed())

        return self

    def enable_timestamp(self, enable):
        self.timestamp = enable
        return self

    def set_image(self, snapshot):
        if snapshot and len(snapshot) == 2:
            self.embeds[-1].set_image(snapshot)
        return self

    def get_embeds(self):
        # Finalise changes to embeds
        self.embeds[-1].timestamp = self.timestamp

        for embed in self.embeds:
            embed.color = self.color
            if self.author:
                embed.set_author(self.author)

        return self.embeds

    def __str__(self):
        string = ""
        for embed in self.get_embeds():
            string += str(embed)


class Embed:
    def __init__(self):
        self.embed_length = 0
        self.color = COLOR_INFO
        self.title = None
        self.description = None
        self.timestamp = True
        self.fields = []
        self.image = None
        self.files = []
        self.author = None

    def set_author(self, author):
        current_length = 0
        if self.author:
            current_length = len(self.author['name'])
        if self.embed_length - current_length + len(author['name']) > MAX_EMBED_LENGTH:
            return False
        self.embed_length -= current_length
        self.author = author
        self.embed_length += len(self.author['name'])
        return True

    def set_title(self, title):
        current_length = 0
        if self.title:
            current_length = len(self.title)
        if self.embed_length - current_length + len(title) > MAX_EMBED_LENGTH:
            return False
        self.embed_length -= current_length
        self.title = title
        self.embed_length += len(self.title)
        return True

    def set_description(self, description):
        current_length = 0
        if self.description:
            current_length = len(self.description)
        if self.embed_length - current_length + len(description) > MAX_EMBED_LENGTH:
            return False
        self.embed_length -= current_length
        self.description = description
        self.embed_length += len(self.description)
        return True

    def add_field(self, field):
        if len(self.fields) == MAX_NUM_FIELDS:
            return False

        field_length = 0
        if 'name' in field and field['name']:
            field_length += len(field['name'])
        if 'value' in field and field['value']:
            field_length += len(field['value'])

        if self.embed_length + field_length > MAX_EMBED_LENGTH:
            return False

        self.fields.append(field)
        self.embed_length += field_length
        return True

    def set_image(self, snapshot):
        self.image = {'url': "attachment://%s" % snapshot[0]}
        self.files.append(snapshot)
        pass

    def get_embed(self):
        embed = {'fields': self.fields}
        if self.author:
            embed['author'] = self.author
        if self.title:
            embed['title'] = self.title
        if self.description:
            embed['description'] = self.description
        if self.timestamp:
            embed['timestamp'] = datetime.datetime.utcnow().isoformat()
        if self.color:
            embed['color'] = self.color
        if self.image:
            embed['image'] = self.image
        return embed

    def get_files(self):
        return self.files

    def __str__(self):
        embed = self.get_embed()
        string = "\n---------------------------------\n"
        if 'author' in embed:
            string += "~~Author~~~~~~~~~~~~~~~~~~\n"
            if 'name' in embed['author']:
                string += "\tAuthor Name: %s\n" % embed['author']['name']
            if 'url' in embed['author']:
                string += "\tAuthor Url: %s\n" % embed['author']['url']
            if 'icon_url' in embed['author']:
                string += "\tAuthor Icon: %s\n" % embed['author']['icon_url']
            string += "~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
        if 'color' in embed:
            string += "Color: %x\n" % embed['color']
        if 'title' in embed:
            string += "Title: %s\n" % embed['title']
        if 'description' in embed:
            string += "Description: %s\n" % embed['description']
        for field in embed['fields']:
            string += "~~~Field~~~~~~~~~~~~~~~~~~\n"
            if 'name' in field:
                string += "\tField Name: %s\n" % field['name']
            if 'value' in field:
                string += "\tField Value: %s\n" % field['value']
            string += "~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
        if 'image' in embed:
            string += "Attached image: %s\n" % embed['image']['url']
        if 'timestamp' in embed:
            string += "Timestamp: %s\n" % embed['timestamp']
        string += "---------------------------------\n"
        return string

