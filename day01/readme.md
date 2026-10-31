# Noa Sofer Sali – Personal Website

My personal website, built with GitHub Pages as the first assignment in my Python course.

**Live site:** https://noasofersali.github.io/

## The Goal

Build a personal website where **content and design are kept separate**:
- Content (text, photos, links) lives in its own files (index.md).
- Design (colors, fonts, layout) lives in a separate CSS file.
- Skeleton for the website livse in layouts, default.html

This way the text can change without touching the design, and the design can change without touching the text.

## How It Works

GitHub Pages runs **Jekyll**, a tool that combines my content with a page layout and design, and publishes the result as a website every time I commit a change.

## File Structure

| File | Role |
|---|---|
| `index.md` | Page content, written in Markdown |
| `_layouts/default.html` | Page frame: loads the CSS and places the content and footer |
| `_data/contacts.yml` | Contact details shown in the footer |
| `assets/css/main.css` | All design: colors, fonts, spacing, photo styles |
| `assets/css/*.jpg` | Photos |

## What I Built

- **Content sections:** About Me, Research Interests, My Goals in This Class, Outside of Work
- **Header:** name, italic subtitle, and a square profile photo, with a blue line underneath
- **Photos:** styled with CSS classes (`profile-photo` for a square photo, `side-photo` for a round one with text wrapping beside it)
- **Links:** thin blue underline and a highlight on hover
- **Footer:** contact info with icons, generated automatically from `contacts.yml`, so new contacts only need to be added to that list

## Lessons Learned

- Name the CSS file `main.css`, not `style.css`, because GitHub's default theme overwrites `style.css`.
- File names must match exactly, including capitals and extensions. Windows may hide a duplicate `.jpg`.
- Folders starting with `_` are not published, so photos must go in `assets`.
- Every CSS block needs both `{` and `}`.
- Check changes in an incognito window or with a hard refresh (Ctrl+F5), because browsers cache old versions.
