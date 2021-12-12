# Pixelation Pro: by Judith Chang and Tony Potchernikov
# December 12, 2021
# Design Document

## Purpose of Project
The overarching purpose of the project was to provide a unique way for artists to share their work online. Typically, artists produce bodies of work that are meant to go together as a set (e.g., think of the way galleries show related works that go together). However, most digital mediums do not provide a centralized digital ‘museum’ for an artist to easily and readily share their works as a complete, stand alone gallery.

This project, as a result, tries to provide a way for artists to set up digital galleries where they can upload images of their work to be shared, as well as provide a way to view, search, and comment on other galleries.

We chose to use python and flask as this provided the most complete set of tools to create a consistent experience.

## Implementing Login and Registration Page:
The login pages and registration pages were executed as similarly done in Week 9 with finance. However, we made a slight change of using “flash()” to show error messages instead of the apology page. This is because using “flash” and reloading the webpage allowed the user to easily re-enter their credentials instead of having to navigate back to the login/registration pages, which creates a tedious and clunky user experience. We wanted all users to log in to use the site as a way to make sure only registered users are viewing pages.

## Implementing Userpage
Upon logging in, the users are taken to the userpage. This userpage was designed to be a central hub for the user, providing a place to search the website for other galleries. We designed the webpage to give a message if no galleries have been created yet to give feedback to the user. If the user has previously created galleries, we set up the page to load all of their galleries as buttons that they can press to go to the corresponding edit page. We also provided a button to create a new gallery. A final, interesting feature is the ability to upload a profile picture and bio (both of which must be submitted together for the information to be uploaded properly), so that other users can read more about the artist when visiting the gallery.

## Implementing Adding and Editing Gallery
We added features for users to be able to add and edit their galleries.

### Adding gallery:
Upon pressing the "Add Gallery" button, users will be brought to a webpage that has a form to provide a gallery title, picture, and picture name. We required all these fields to be filled in before the gallery can be created since a gallery should have at least one piece in it, and we needed the photos and galleries to have unique, identifiable names (case sensitive) to query with/ pull from the database. We also added provisions to make sure users do not reuse the same gallery name (case sensitive) to make sure that there are no errors when pulling gallery information from the database. There will be a user error if more than one photo in the same gallery have the exact same name (case sensitive). Additionally, there will be a user error if more than one gallery from the same user has the same name (case sensitive).

### Editing gallery
Users can go to (or can be redirected to) the edit page of the gallery. This page provides ways for the user to view/delete/change the name of their photos. We designed this feature so that each photo has its own hidden and unique photo_id embedded in the website so that when the user tries to delete a photo, the website will delete the correct photo. And we did a similar thing for updating the photo name. However, we added code that makes sure the same photo name is not used within the same gallery so that there are no errors/issues when loading the page. Additionally, there is a feature to rename the gallery, which functions similarly to the renaming of the photo feature. And there is a feature to delete the gallery, which was done by using a post request to another route that deletes the photos in the gallery, the gallery itself, and then redirects the user. This was all done to give the user full functionality and ability to fully edit their gallery.

## Implementing Searching
We opted to have a search function to allow users to search for galleries. This search uses a get request since we thought there was no need for added security while searching, and it provided a way to tie buttons (e.g., for the top three most visited pages) to a specific gallery page using a specified link (e.g. “/gallery?g=[gallery#]). We wanted the search to primarily search galleries to emphasize interacting with a variety of galleries, but if users do not have a specific gallery in mind to visit, they can opt to press the “View All Galleries” button, which shows all galleries on the website in descending order of views. This way the user can see and select any gallery they want to visit if unsure of where to start. The search function is provided on all key pages: userpage (so users can initiate search), search results page (so users can modify search), and gallery page (in case users want to search more from the gallery page). Search queries are not deliberately possible from the edit page or “add new gallery” page to focus the user’s attention on the functionality of those pages.

### A special note on three most visited pages:
We thought this feature could be an interesting way for users to engage with the website and as a starting point for users to visit other pages. We did this by having the pages with search bars also load the top three most visited pages. Views were tracked by updating the views count in the corresponding database slot every time a user loads the gallery page (view count updates by 1 as long as the user is NOT the creator of the gallery, since we did not want the original creator to attempt to artificially increase their page views).

### A special note on artist queries:
We wanted to provide a way for users to learn more about the artist and see more works by an artist:

#### Artist info
If the user provided a profile pic and bio, each gallery of that user will display this profile information at the bottom of the gallery page so that visitors can read more about them.

#### Hyperlinked Artist Name:
 The artist name is hyperlinked at the end of the gallery to allow visiting users to view all of the artist's other works. This link acts as an embedded search query that uses a slightly different GET request  (using ‘a’ as the key) to search the database for galleries based on the artist's username. Because we added this feature, we also added additional code that handles situations in whcih the user manually attempts to force a simultaneous gallery and artist search query (i.e. situation like: “/search?q=kong&a=Sally”) in order to get useful search results, and prevent the website from crashing.

## Viewing Galleries
After searching and clicking on a gallery of interest, we had the page load to the gallery site where the user can view the images, see information about the artist, and leave comments. We also coded a feature that redirects users to the edit page of a gallery if they are the creator of that gallery. That way they can manage the content of their gallery instead.

### Commenting
We wanted users to be able to comment on the page, so we created a database to keep track of and store comments. We provided a box at the bottom so users are able to leave new comments as well. We opted to keep the comments anonymous as a way to make commenting easier and less pressuring. Once the user submits their comments (and assuming the comment box is not empty) the comment will be saved in the comment database and page reloaded.