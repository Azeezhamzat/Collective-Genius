import django from 'django'
import React from 'react'
import { updateItem } from './helpers.js'
import QuestionUser from './livequestion_user'
import QuestionModerator from './livequestion_moderator'

export default class StatisticsBox extends React.Component {
  constructor (props) {
    super(props)
    this.state = { answeredQuestions: props.answeredQuestions }
  }

  componentDidUpdate (prevProps) {
    if (this.props.answeredQuestions !== prevProps.answeredQuestions) {
      this.setState({ answeredQuestions: this.props.answeredQuestions })
    }
  }

  updateQuestion (data, id) {
    const url = this.props.questions_api_url + id + '/'
    return updateItem(data, url, 'PATCH')
  }

  removeFromList (id, data) {
    this.updateQuestion(data, id)
      .then(response => this.setState(prevState => ({
        answeredQuestions: prevState.answeredQuestions.filter(question => question.id !== id)
      })))
  }

  countCategory (category) {
    let countPerCategory = 0
    let answeredQuestions = 0
    this.props.answeredQuestions.forEach(function (question) {
      if (question.is_answered && !question.is_hidden) {
        answeredQuestions++
        if (question.category === category) {
          countPerCategory++
        }
      }
    })
    return Math.round(countPerCategory * 100 / answeredQuestions) || 0
  }

  getTopLiked () {
    return [...this.props.answeredQuestions]
      .sort((a, b) => b.likes.count - a.likes.count)
      .slice(0, 5)
  }

  render () {
    const questionAnsweredTag = django.gettext('Questions Answered')
    const topLikedTag = django.gettext('Most liked answered questions')
    const likesTag = django.gettext('likes')
    const topLiked = this.getTopLiked()
    const maxLikes = topLiked.length > 0 ? topLiked[0].likes.count : 0
    return (
      <div>
        {this.props.categories.length > 0 &&
          <div className="row justify-content-center py-4">
            <div className="col-12 col-md-8">
              {this.props.categories.map((category, index) => {
                const countPerCategory = this.countCategory(category)
                const style = { width: countPerCategory + '%' }
                return (
                  <div key={index} className="mt-3">
                    <span>{category}</span>
                    <div className="progress">
                      <div
                        className="progress-bar" style={style} role="progressbar" aria-valuenow="25" aria-valuemin="0"
                        aria-valuemax="100"
                      >{countPerCategory}%
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>}
        {maxLikes > 0 &&
          <div className="row justify-content-center py-4">
            <div className="col-12 col-md-8">
              <h3 className="u-serif-header text-center mb-3">{topLikedTag}</h3>
              <ul className="livequestion-statistics__barlist">
                {topLiked.map((question, index) => {
                  const pct = Math.round(question.likes.count * 100 / maxLikes)
                  return (
                    <li key={question.id}>
                      <span className="livequestion-statistics__barlist-label">{question.text}</span>
                      <div className="livequestion-statistics__barlist-row">
                        <div className="livequestion-statistics__barlist-track">
                          <div className="livequestion-statistics__barlist-fill" style={{ width: pct + '%' }} />
                        </div>
                        <span className="livequestion-statistics__barlist-value">{question.likes.count} {likesTag}</span>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </div>
          </div>}
        <h3 className="u-serif-header text-center mt-5">{questionAnsweredTag}</h3>
        {this.props.isModerator
          ? (
            <div className="list-group mt-md-4">
              {this.state.answeredQuestions.map((question, index) => {
                return (
                  <QuestionModerator
                    updateQuestion={this.updateQuestion.bind(this)}
                    displayIsOnShortlist={false}
                    displayIsLive={false}
                    displayIsHidden={false}
                    displayIsAnswered={question.is_answered}
                    removeFromList={this.removeFromList.bind(this)}
                    key={question.id}
                    id={question.id}
                    is_answered={question.is_answered}
                    is_on_shortlist={question.is_on_shortlist}
                    is_live={question.is_live}
                    is_hidden={question.is_hidden}
                    category={question.category}
                    likes={question.likes}
                  >
                    {question.text}
                  </QuestionModerator>
                )
              })}
            </div>
            )
          : (
            <div className="list-group mt-3 mt-md-4">
              {this.state.answeredQuestions.map((question, index) => {
                return (
                  <QuestionUser
                    key={question.id}
                    id={question.id}
                    is_answered={question.is_answered}
                    is_on_shortlist={question.is_on_shortlist}
                    is_live={question.is_live}
                    is_hidden={question.is_hidden}
                    category={question.category}
                    likes={question.likes}
                  >
                    {question.text}
                  </QuestionUser>
                )
              })}
            </div>
            )}
      </div>
    )
  }
}
