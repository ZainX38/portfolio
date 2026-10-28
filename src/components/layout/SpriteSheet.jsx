import sprite from '../../assets/sprites.svg?raw'

// Puts every <symbol> into the page itself, so icons render instantly
// instead of waiting for a separate request for sprites.svg
function SpriteSheet() {
    return (
        <div
            aria-hidden="true"
            style={{ position: 'absolute', width: 0, height: 0, overflow: 'hidden' }}
            dangerouslySetInnerHTML={{ __html: sprite }}
        />
    )
}

export default SpriteSheet