#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_migrate import Migrate
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
from models import db, Venue, Artist, Show

logging.basicConfig(level=logging.INFO)
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  areas = Venue.query.with_entities(Venue.city, Venue.state).distinct()
  data = []
  logging.info(f'Processing {len(areas.all())} areas')
  for area in areas:
    logging.info(f'Processing area: {area.city}, {area.state}')
    venues = Venue.query.filter_by(city=area.city, state=area.state).all()
    venues_data = []
    for venue in venues:
      num_upcoming_shows = Show.query.filter(Show.venue_id == venue.id, Show.start_time > datetime.now()).count()
      venues_data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": num_upcoming_shows
        })
    data.append({
      "city": area.city,
      "state": area.state,
      "venues": venues_data
      })
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  response = {
    "count": len(venues),
    "data": []
    }
  for venue in venues:
    num_upcoming_shows = len([show for show in venue.shows if show.start_time > datetime.now()])
    response["data"].append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": num_upcoming_shows,
      })
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  if not venue:
    return render_template('errors/404.html'), 404
  
  past_shows_query = Show.query.join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()
  upcoming_shows_query = Show.query.join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()
  past_shows = [{
    "artist_id": show.artist_id,
    "artist_name": show.Artist.name,
    "artist_image_link": show.Artist.image_link,
    "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    } for show in past_shows_query]

  upcoming_shows = [{
    "artist_id": show.Artist_id,
    "artist_name": show.Artist.name,
    "artist_image_link": show.Artist.image_link,
    "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    } for show in upcoming_shows_query]

  venue_data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
    }

  return render_template('pages/show_venue.html', venue=venue_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  try:
    new_venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
                image_link=form.image_link.data,
                website=form.website_link.data,
                seeking_talent=form.seeking_talent.data,
                seeking_description=form.seeking_description.data
                )
    db.session.add(new_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    logging.info(f'Failed to create artist')
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    print('Delete Venue', venue.name)
    if venue:
      db.session.delete(venue)
      db.session.commit()
      print('Delete Venue', venue.name)
      # flash(f'Venue {venue.name} was successfully deleted.')
      return jsonify({'success': True})
    else:
      # flash('Venue not found.')
      return jsonify({'success': False}), 500
  except Exception as e:
    print('Oop rolling back Delete Venue', e)
    db.session.rollback()
    # flash('An error occurred. Venue could not be deleted.')
  finally:
      db.session.close()


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artist_query = Artist.query.all()
  data = [{"id": artist.id, "name": artist.name} for artist in artist_query]
  logging.info(f'Processing {len(data)} artist')
  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  artist_query = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  response_data = []
  for artist in artist_query:
    num_upcoming_shows = Show.query.filter(Show.artist_id == artist.id, Show.start_time > datetime.now()).count()
    response_data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": num_upcoming_shows,
      })
  response = {
        "count": len(artist_query),
        "data": response_data
    }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

from datetime import datetime

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  if not artist:
    return render_template('errors/404.html'), 404
  
  past_shows_query = Show.query.join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()
  upcoming_shows_query = Show.query.join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()
  past_shows = [{
    "venue_id": show.Venue.id,
    "venue_name": show.Venue.name,
    "venue_image_link": show.Venue.image_link,
    "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    } for show in past_shows_query]

  upcoming_shows = [{
    "venue_id": show.Venue.id,
    "venue_name": show.Venue.name,
    "venue_image_link": show.Venue.image_link,
    "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    } for show in upcoming_shows_query]

  artist_data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
    }
  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
  if form.validate():
    artist = Artist.query.get(artist_id)
    if artist:
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.genres = form.genres.data
      artist.facebook_link = form.facebook_link.data
      artist.image_link = form.image_link.data
      artist.website_link = form.website_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data

      try:
        db.session.commit()
        flash(f'Artist {form.name.data} was successfully updated!')
      except:
        db.session.rollback()
        flash(f'An error occurred. Artist {form.name.data} could not be updated.')
      finally:
        db.session.close()
    else:
        flash('Artist not found.')
  else:
    flash('Form data is not valid, please correct the errors and try again.')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  venue = Venue.query.get(venue_id)
  if venue:
    try:
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.genres = form.genres.data
      venue.facebook_link = form.facebook_link.data
      venue.image_link = form.image_link.data
      venue.website = form.website_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data
            
      db.session.commit()
      flash(f'Venue {form.name.data} was successfully updated!')
    except:
      db.session.rollback()
      flash(f'An error occurred. Venue {form.name.data} could not be updated.')
    finally:
      db.session.close()
  else:
    flash('Venue not found.')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm(request.form)
    try:
      new_artist = Artist(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        genres=form.genres.data,
        facebook_link=form.facebook_link.data,
        image_link=form.image_link.data,
        website=form.website_link.data,
        seeking_venue=form.seeking_venue.data,
        seeking_description=form.seeking_description.data
        )
      db.session.add(new_artist)
      db.session.commit()
      flash('Artist ' + form.name.data + ' was successfully listed!')
    except Exception as e:
      db.session.rollback()
      logging.info(f"An error occurred: {str(e)}")
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    finally:
      db.session.close()
    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------


from datetime import datetime

@app.route('/shows')
def shows():
  shows_query = Show.query.join(Artist).join(Venue).all()
  data = []
  for show in shows_query:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.Venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.Artist.name,
      "artist_image_link": show.Artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    try:
      new_show = Show(
        artist_id=form.artist_id.data,
        venue_id=form.venue_id.data,
        start_time=form.start_time.data
        )
      db.session.add(new_show)
      db.session.commit()
      flash('Show was successfully listed!')
    except:
      db.session.rollback()
      flash('An error occurred. Show could not be listed.')
    finally:
       db.session.close()
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
