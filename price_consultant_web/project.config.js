const path = require('path')
const NODE_ENV = process.env.NODE_ENV || 'development'

module.exports = {
    env: NODE_ENV,
    basePath: path.resolve('static/src/consultant_price/'),
    srcDir: 'src',
    main: 'index',
    outDir: 'static/src/components/js/',
    publicPath: '/',
    sourcemaps: NODE_ENV == 'development' ? true : false,
    vendors: []
}
