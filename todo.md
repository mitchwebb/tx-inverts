## TODO

### Database

- [ ] Finalize and document schema
- [x] Add `ns_rank_state` column
- [x] Get to work on automatic update capabilities (observations)
- [ ] Get to work on manual update pipeline (taxonomy)
- [x] Index frequently queried fields (`taxon_id`, etc.)
- [ ] Store common names in DB
- [x] List of invasives — Store in database
- [ ] Handle 'indet.' species
- [ ] Common Names!
- [ ] Need a date_added column to allow rollback
- [ ] Differences in handling conn (get_single)

### Map Layers

- [x] Tiled observation layer via PostGIS
- [ ] Add vector layer for user-submitted points
- [x] Compute and display range extent
- [x] Compute and display area of occupancy
- [ ] Enable adding points by map click
- [ ] Multiple Species
- [ ] Adjustable occurrence radius
- [ ] Adjustable AOO size
- [ ] Change rankings verbiage
- [ ] Note about not including thread/trends
- [x] Layers key in foldout
- [ ] GBIF Species Link

### Testing & Dev UX

- [ ] Testing in general

### Functionality

- [ ] Apply filters to ranking (re-run ranking)
- [ ] Mobile
- [ ] Improve date input functionality (min-max unclear in native components)
- [ ] Variable AOO Bin Sizes (Requires server interaction to get values)

### Documentation

- [ ] Add usage instructions to README
- [ ] Document DB schema
- [ ] Add endpoint specs

### Questions

- [ ] How does range extent work when dealing with boundaries like states?

### BUGS

- [ ] Map width needs a minimum (minimum width for header bar)
