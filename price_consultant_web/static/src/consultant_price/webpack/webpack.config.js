const path = require('path')
const webpack = require('webpack')
const TerserPlugin = require('terser-webpack-plugin');
const project = require('../../../../project.config.js')
const inProject = path.resolve.bind(path, project.basePath)
const inProjectSrc = (file) => inProject(project.srcDir, file)

const __PROD__ = project.env === 'production'

const webpackConfig = {
	mode: project.env,
	entry: {
		main: [
			inProjectSrc(project.main)
		]
	},
  devtool: project.sourcemaps ? 'source-map': false,
  performance: {
    hints: false,
  },
	module: {
		rules: [],
	},
  optimization: {
    minimize: __PROD__ ? true: false,
    mangleWasmImports: true,
    concatenateModules: __PROD__ ? true: false,
    runtimeChunk: 'single',
    splitChunks: {
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all'
        }
      }
    },
    minimizer: []
  },
  resolve: {
      modules: [
      inProject(project.srcDir),
      'node_modules',
      ],
      extensions: ['*', '.js', '.jsx', '.json'],
  },
	plugins: [
		new webpack.DefinePlugin({
			'process.env': {
				NODE_ENV: JSON.stringify(project.env),
			},
		}),
	],
	output: {
		filename: __PROD__ ? '[name].min.js': '[name].js',
		path: path.resolve(project.outDir),
		publicPath: project.publicPath,
	},
}

// Rules
// ----------
webpackConfig.module.rules.push(
    {
        test: /\.(jsx|js)$/,
        exclude: /node_modules/,
        use: [{
            loader: 'babel-loader',
            options: {
                presets: [
                    '@babel/preset-env',
                    ['@babel/preset-react', {"runtime": "automatic"}]
                ]
            }
        }]
    },
    {
      test: /\.(png|jpg|gif)$/i,
      use: [
        {
          loader: 'url-loader',
          options: {
            limit: 8192,
          },
        },
        {
          loader: 'file-loader',
        },
      ],
    },
    {
      test: /\.(less|css|scss|sass)$/i,
      use: [
          { loader: "style-loader" },
          { loader: "css-loader" },
          { loader: "sass-loader" },
          // {
          //   loader: 'resolve-url-loader',
            // options: {
            //   sourceMap: project.sourcemaps,
            // }
          // },
          {
            loader: "less-loader",
            options: {
                lessOptions: {
                    javascriptEnabled: true,
                }
            }
          },
      ]
    },
)

// Production
if(__PROD__){
  webpackConfig.optimization.minimizer.push(
    new TerserPlugin({
      parallel: true,
      terserOptions: {
        ecma: undefined,
        parse: {},
        compress: {},
        mangle: true,
        module: false,
        output: null,
        format: null,
        toplevel: false,
        nameCache: null,
        ie8: false,
        keep_classnames: undefined,
        keep_fnames: false,
        safari10: false,
      },
    }),
  )
}

module.exports = webpackConfig